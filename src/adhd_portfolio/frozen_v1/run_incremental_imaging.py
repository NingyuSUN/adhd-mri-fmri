"""Validation-selected score fusion; existing locked15fold checkpoints, no retraining."""
from pathlib import Path
import sys
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE/'vendor/connectome0121'))
import argparse,json,time,traceback
import numpy as np
import pandas as pd
import joblib,torch
from sklearn.covariance import LedoitWolf
from sklearn.metrics import roc_auc_score
from nilearn.connectome import sym_matrix_to_vec
from threadpoolctl import threadpool_limits
from run_functional_fusion import MLP,predict,save_json,digest
from run_tcn_fc_completion import load_data
from run_repeated_connectome import partitions,controls
from refine_tangent_reference import transform

PARENT=BASE/'runs/repeated_connectome_20260907_locked5'
ALPHAS=[0.,.25,.5,.75,1.]

def choose_alpha(y,base,image):
    aucs=[float(roc_auc_score(y,(1-a)*base+a*image)) for a in ALPHAS]
    best=next(i for i,v in enumerate(aucs) if v>=max(aucs)-1e-12)
    return ALPHAS[best],aucs

def conditional_auc(g):
    # Only within-site positive-negative pairs contribute. Never compare across sites.
    terms=[]
    for _,h in g.groupby('site'):
        pairs=int(h.y.sum()*(len(h)-h.y.sum()))
        if pairs:terms.append((pairs,roc_auc_score(h.y,h.score)))
    return sum(w*a for w,a in terms)/sum(w for w,a in terms)

def summarize(out):
    p=pd.read_csv(out/'predictions.csv')
    assert len(p)==378*5*5 and not p.duplicated(['repeat','model','subject_id']).any()
    fm=pd.DataFrame([dict(repeat=r,fold=f,model=m,auc=roc_auc_score(g.y,g.score),within_site_auc=conditional_auc(g)) for (r,f,m),g in p.groupby(['repeat','fold','model'])])
    fm.to_csv(out/'fold_metrics.csv',index=False)
    rm=fm.groupby(['repeat','model'])[['auc','within_site_auc']].mean().reset_index();rm.to_csv(out/'repeat_metrics.csv',index=False)
    summary=rm.groupby('model').agg(mean_auc=('auc','mean'),sd_repeat_auc=('auc','std'),min_repeat_auc=('auc','min'),max_repeat_auc=('auc','max'),mean_within_site_auc=('within_site_auc','mean'));summary.to_csv(out/'summary.csv')
    contrasts=[]
    for metric in ['auc','within_site_auc']:
        w=rm.pivot(index='repeat',columns='model',values=metric)
        for name in ['fusion_tangent_lr','fusion_tangent_mlp']:
            d=w[name]-w['site_motion_lr']
            contrasts.append(dict(metric=metric,candidate=name,reference='site_motion_lr',mean_delta=d.mean(),min_delta=d.min(),max_delta=d.max(),positive_repeats=int((d>1e-12).sum()),negative_repeats=int((d< -1e-12).sum()),total=5))
    pd.DataFrame(contrasts).to_csv(out/'paired_deltas.csv',index=False)
    selections=pd.read_csv(out/'selection.csv');selections[selections.selected].groupby(['image_model','alpha']).size().rename('folds').to_csv(out/'alpha_counts.csv')
    (out/'REPORT.md').write_text('# Exploratory incremental imaging experiment\n\n'+summary.to_string()+'\n\n'+pd.DataFrame(contrasts).to_string(index=False)+'\n\nFixed five repeat / three fold internal partitions. Validation-only alpha selection, ties prefer lower imaging weight. Both LR predict_proba values and MLP sigmoid outputs are uncalibrated, including class-balanced training. No probability or clinical-risk calibration claim. Within-site AUC uses only same-site positive-negative pairs, weighted by pair counts in each fold; excludes cross-site pairs but does not fully control motion or other confounding. Adaptive reuse of data and validation sets: no untouched external validation, significance or causal interpretation. Repeat range is not a confidence interval.\n',encoding='utf-8')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    if (out/'status.json').exists():raise RuntimeError('Refusing duplicate run')
    def status(stage,**kw):save_json(out/'status.json',dict(status=stage,updated=time.strftime('%Y-%m-%d %H:%M:%S'),**kw))
    try:
        status('preparing');torch.set_num_threads(4)
        assert json.loads((PARENT/'status.json').read_text())['status']=='complete_replay_checked'
        c=pd.read_csv(PARENT/'cohort.csv');y=c.label.to_numpy(np.int64);parts=list(partitions(c))
        save_json(out/'protocol.json',dict(parent=str(PARENT),n=378,folds=15,alphas=ALPHAS,primary='fusion_tangent_mlp minus site_motion_lr mean fold AUC',secondary='fusion_tangent_lr; within-site pair-weighted AUC',fusion='(1-alpha)*site_motion_LR.predict_proba + alpha*imaging_probability',selection='validation AUC only; earliest tie prefers less imaging; no new checkpoint/feature/epoch/C selection',calibration='none; scores not calibrated risks',scope='Reuse fixed existing models and15partitions; no fitting on test or new neural training',caveat='Adaptive exploratory internal reuse, validation already used for checkpoint/C selection; not independent external validation or causal confound elimination',split_sha256=digest(PARENT/'splits.csv'),source_sha256=digest(Path(__file__))))
        for name in ['cohort.csv','splits.csv']:(out/name).write_bytes((PARENT/name).read_bytes())
        (out/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
        status('loading_data');actual,_,series,fc,edges,_=load_data();del fc,edges
        assert c.subject_id.tolist()==actual.subject_id.tolist()
        with threadpool_limits(limits=4):
            cov=[]
            for i in series.indices:
                d=np.asarray(series.base.data[series.base.offsets[i]:series.base.offsets[i+1]],dtype=np.float64)
                cov.append(LedoitWolf(store_precision=False).fit(d).covariance_)
            del series
            cov=np.asarray(cov);old=pd.read_csv(PARENT/'predictions.csv');preds=[];selections=[];audit=[]
            for repeat,fold,tr,va,te in parts:
                status('reconstructing_predictions',repeat=repeat,fold=fold,completed_folds=len(audit))
                folder=PARENT/f'repeat{repeat}_fold{fold}'
                ref=joblib.load(folder/'reference.joblib');tf=joblib.load(folder/'tangent_transform.joblib')
                cf=joblib.load(folder/'controls.joblib');fit_ids=c.subject_id.iloc[tr].tolist()
                assert ref['fit_ids']==tf['fit_ids']==cf['fit_ids']==fit_ids
                white,logs=transform(cov,ref['mean']);np.testing.assert_allclose(white,ref['white'],atol=1e-10)
                residual=float(np.linalg.norm(logs[tr].mean(0))/ref['mean'].size);assert residual<1e-7
                raw=sym_matrix_to_vec(logs,discard_diagonal=True).astype(np.float32);del logs
                x=tf['scaler'].transform(raw[:,tf['order']]).astype(np.float32);del raw
                ctr,_=controls(c,tr);z=ctr['site_motion_lr']
                base=joblib.load(folder/'site_motion_lr.joblib');lr=joblib.load(folder/'tangent_lr.joblib')
                scores={'site_motion_lr':base.predict_proba(z)[:,1],'tangent_lr':lr.predict_proba(x)[:,1]}
                xt=torch.from_numpy(x);mlps=[]
                for seed in [1200+fold,2200+fold,3200+fold]:
                    checkpoint=torch.load(folder/f'fold{fold}_tangent_mlp_seed{seed}.pt',weights_only=True)
                    model=MLP(checkpoint['input_features']);model.load_state_dict(checkpoint['state_dict'])
                    mlps.append(predict(model,xt,np.arange(len(c))))
                scores['tangent_mlp']=np.mean(mlps,axis=0)
                previous=old[old.repeat.eq(repeat)&old.fold.eq(fold)]
                for name,new in [('site_motion_lr',base.decision_function(z[te])),('tangent_lr',lr.decision_function(x[te])),('tangent_mlp_ens',scores['tangent_mlp'][te])]:
                    saved=previous[previous.model.eq(name)].set_index('subject_id').loc[c.subject_id.iloc[te]].score.to_numpy()
                    np.testing.assert_allclose(saved,new,rtol=1e-5,atol=1e-6)
                for image in ['tangent_lr','tangent_mlp']:
                    a,aucs=choose_alpha(y[va],scores['site_motion_lr'][va],scores[image][va])
                    selections.extend(dict(repeat=repeat,fold=fold,image_model=image,alpha=alpha,validation_auc=v,selected=alpha==a) for alpha,v in zip(ALPHAS,aucs))
                    scores['fusion_'+image]=(1-a)*scores['site_motion_lr']+a*scores[image]
                for name,s in scores.items():
                    preds.extend(dict(repeat=repeat,fold=fold,model=name,subject_id=c.subject_id.iloc[i],site=c.site.iloc[i],y=int(y[i]),score=float(s[i])) for i in te)
                # Retain validation scores for independently replaying alpha selection.
                vrows=[dict(model=name,subject_id=c.subject_id.iloc[i],y=int(y[i]),score=float(s[i])) for name,s in scores.items() for i in va]
                pd.DataFrame(vrows).to_csv(out/f'repeat{repeat}_fold{fold}_validation.csv',index=False)
                audit.append(dict(repeat=repeat,fold=fold,residual=residual,source_predictions_replayed=True,train_fit_ids_checked=True))
                for name,rows in [('predictions',preds),('selection',selections),('audit',audit)]:pd.DataFrame(rows).to_csv(out/(name+'.csv'),index=False)
                print('COMPLETE FOLD',repeat,fold,'metrics withheld',flush=True)
        summarize(out);status('complete_replay_checked',completed_folds=15)
    except BaseException as e:status('failed',error=repr(e));traceback.print_exc();raise

if __name__=='__main__':main()
