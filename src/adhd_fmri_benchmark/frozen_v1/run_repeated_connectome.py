"""Locked repeated internal CV; training-only geometry and confound controls."""
from pathlib import Path
import sys
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE/'vendor/connectome0121'))
import argparse,json,time,warnings,traceback
import numpy as np
import pandas as pd
import joblib,torch
from scipy.stats import spearmanr
from sklearn.model_selection import StratifiedKFold,train_test_split
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.covariance import LedoitWolf
from nilearn.connectome import sym_matrix_to_vec
from nilearn.connectome.connectivity_matrices import _geometric_mean
from threadpoolctl import threadpool_limits
from run_connectome_representations import select_features,CS
from run_functional_fusion import save_json,digest,train_neural,predict,MLP
from run_tcn_fc_completion import load_data
from refine_tangent_reference import transform

SEEDS=[3101,3102,3103,3104,3105]
OLD=BASE/'runs/connectome_representations_20260907_165559'

def partitions(c):
    strata=c.site.astype(str)+'__'+c.label.astype(int).astype(str)
    assert strata.value_counts().min()>=3
    for repeat,seed in enumerate(SEEDS,1):
        tests=[]
        for fold,(tv,te) in enumerate(StratifiedKFold(3,shuffle=True,random_state=seed).split(c,strata),1):
            tr,va=train_test_split(tv,test_size=.2,stratify=c.label.to_numpy()[tv],random_state=seed*10+fold)
            assert [len(tr),len(va),len(te)]==[201,51,126]
            assert not(set(tr)&set(va) or set(tr)&set(te) or set(va)&set(te))
            assert set(c.site.iloc[tr])==set(c.site)
            for ix in [tr,va,te]: assert set(c.label.iloc[ix])=={0,1}
            tests.extend(te)
            yield repeat,fold,tr,va,te
        assert sorted(tests)==list(range(len(c)))

def controls(c,tr):
    enc=OneHotEncoder(handle_unknown='ignore',sparse_output=False).fit(c[['site']].iloc[tr])
    site=enc.transform(c[['site']])
    raw=c[['mean_fd','pct_fd_gt_0p2','mean_dvars']].to_numpy(dtype=float,copy=True)
    raw[~np.isfinite(raw)]=np.nan
    imp=SimpleImputer(strategy='median',keep_empty_features=True).fit(raw[tr])
    motion=np.column_stack([imp.transform(raw),np.isnan(raw).astype(float)])
    scale=StandardScaler().fit(motion[tr]);motion=scale.transform(motion)
    return {'site_only_lr':site,'motion_only_lr':motion,'site_motion_lr':np.column_stack([site,motion])},dict(encoder=enc,imputer=imp,scaler=scale,fit_ids=c.subject_id.iloc[tr].tolist())

def summarize(out,c):
    p=pd.read_csv(out/'predictions.csv');rows=[];sub=[];corr=[]
    assert len(p)==378*5*9
    assert not p.duplicated(['repeat','model','subject_id']).any()
    for (repeat,fold,model),g in p.groupby(['repeat','fold','model']):
        rows.append(dict(repeat=repeat,fold=fold,model=model,auc=roc_auc_score(g.y,g.score)))
        for site,h in g.groupby('site'):
            if h.y.nunique()==2:
                sub.append(dict(repeat=repeat,fold=fold,model=model,subgroup='site:'+site,n=len(h),auc=roc_auc_score(h.y,h.score)))
            valid=h.dropna(subset=['mean_fd'])
            if len(valid)>=10 and valid.mean_fd.nunique()>1 and valid.score.nunique()>1:
                corr.append(dict(repeat=repeat,fold=fold,model=model,site=site,n=len(valid),score_fd_spearman=float(spearmanr(valid.mean_fd,valid.score).statistic)))
        for label,mask in [('low_motion',g.mean_fd.le(g.train_fd_median)),('high_motion',g.mean_fd.gt(g.train_fd_median))]:
            h=g[mask]
            if h.y.nunique()==2:sub.append(dict(repeat=repeat,fold=fold,model=model,subgroup=label,n=len(h),auc=roc_auc_score(h.y,h.score)))
    fm=pd.DataFrame(rows);fm.to_csv(out/'fold_metrics.csv',index=False)
    rm=fm.groupby(['repeat','model']).auc.mean().unstack();rm.to_csv(out/'repeat_metrics.csv')
    summary=rm.agg(['mean','std','min','max']).T;summary.to_csv(out/'summary.csv')
    contrasts=[]
    for a,b in [('tangent_lr','pearson_lr'),('tangent_mlp_ens','pearson_mlp_ens'),('tangent_mlp_ens','tangent_lr'),('tangent_adjusted_lr','site_motion_lr'),('pearson_adjusted_lr','site_motion_lr')]:
        d=rm[a]-rm[b]
        contrasts.append(dict(candidate=a,reference=b,mean_delta=d.mean(),min_delta=d.min(),max_delta=d.max(),positive_repeats=int((d>0).sum()),total_repeats=5))
    pd.DataFrame(contrasts).to_csv(out/'paired_repeat_deltas.csv',index=False)
    pd.DataFrame(sub).to_csv(out/'subgroup_metrics.csv',index=False)
    pd.DataFrame(corr).to_csv(out/'within_site_motion_correlations.csv',index=False)
    (out/'REPORT.md').write_text('# Repeated internal fMRI validation\n\n'+summary.to_string()+'\n\n'+pd.DataFrame(contrasts).to_string(index=False)+'\n\nFive repeated partitions reuse the same people. SD/range are descriptive split sensitivity, not independent-study confidence intervals. No external or LOSO validation. Confound controls and subgroup analyses do not establish causal independence from site or motion. Historical 0.622 is not a paired benchmark. All planned results retained.\n',encoding='utf-8')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--prepare-only',action='store_true');args=ap.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    if (out/'status.json').exists():raise RuntimeError('Existing run: do not duplicate or overwrite')
    def status(stage,**kw):save_json(out/'status.json',dict(status=stage,updated=time.strftime('%Y-%m-%d %H:%M:%S'),**kw))
    try:
        status('preparing');torch.set_num_threads(4)
        c=pd.read_csv(OLD/'cohort.csv');y=c.label.to_numpy(np.int64);parts=list(partitions(c))
        assert len(parts)==15 and c.subject_id.nunique()==378
        c.to_csv(out/'cohort.csv',index=False)
        splitrows=[dict(repeat=r,fold=f,role=role,subject_id=c.subject_id.iloc[i],label=int(y[i]),site=c.site.iloc[i]) for r,f,tr,va,te in parts for role,ix in [('train',tr),('validation',va),('test',te)] for i in ix]
        pd.DataFrame(splitrows).to_csv(out/'splits.csv',index=False)
        protocol=dict(seeds=SEEDS,n=378,outer='5 repeats x 3 folds, site-label stratified',inner='20% label-stratified validation; 201/51/126',primary='tangent_lr minus pearson_lr mean of fold AUC, summarized per repeat',secondary='MLP comparison, site/motion controls, covariate-augmented LR, within-site AUC and score-FD association; low/high FD cutoff from training median',mlp='64/16, original training function, seeds1200+fold,2200+fold,3200+fold fixed across repeats; equal ensemble',linear_C=CS,feature_selection='training-only ANOVA top1000 and scaling',geometry='LedoitWolf within subject; geometric mean fit ONLY train, max100 tol1e-8, independent residual below1e-7 or STOP',test_policy='no test-dependent adaptation; all repeats retained; no pooling margins across folds',interpretation='Adaptively reused internal cohort; repeated folds dependent; SD/range not confidence intervals; not external validation',split_sha256=digest(out/'splits.csv'),cohort_sha256=digest(out/'cohort.csv'),threads=4)
        save_json(out/'protocol.json',protocol)
        for name in [Path(__file__).name,'run_functional_fusion.py','refine_tangent_reference.py','run_connectome_representations.py']:(out/name).write_bytes((BASE/name).read_bytes())
        for r,f,tr,va,te in parts:
            z,_=controls(c,tr);assert all(np.isfinite(x).all() for x in z.values())
        if args.prepare_only:status('prepared_checks_passed');return
        status('loading_verified_data')
        actual,_,series,fc,edges,_=load_data();assert actual.subject_id.tolist()==c.subject_id.tolist();del fc,edges
        data=[np.asarray(series.base.data[series.base.offsets[i]:series.base.offsets[i+1]],dtype=np.float64) for i in series.indices];del series
        predictions=[];searches=[];audits=[];training=[]
        with threadpool_limits(limits=4):
            cov=np.asarray([LedoitWolf(store_precision=False).fit(d).covariance_ for d in data])
            pearson=np.asarray([sym_matrix_to_vec(np.corrcoef(d,rowvar=False),discard_diagonal=True) for d in data],dtype=np.float32);del data
            np.save(out/'pearson.npy',pearson)
            for repeat,fold,tr,va,te in parts:
                tag=f'repeat{repeat}_fold{fold}';folder=out/tag;folder.mkdir()
                status('fitting_tangent',repeat=repeat,fold=fold,completed_folds=len(audits))
                print(tag,'training-only geometry',flush=True)
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter('always');mean=_geometric_mean(cov[tr],max_iter=100,tol=1e-8)
                white,logs=transform(cov,mean);residual=float(np.linalg.norm(logs[tr].mean(axis=0))/mean.size)
                assert residual<1e-7,f'Numerical residual failed: {residual}'
                tx=sym_matrix_to_vec(logs,discard_diagonal=True).astype(np.float32);del logs
                joblib.dump(dict(mean=mean,white=white,fit_ids=c.subject_id.iloc[tr].tolist(),residual=residual,warnings=[str(w.message) for w in caught]),folder/'reference.joblib')
                controls_x,control_fit=controls(c,tr);joblib.dump(control_fit,folder/'controls.joblib')
                features=dict(controls_x)
                for rep,raw in [('pearson',pearson),('tangent',tx)]:
                    x,order,scaler=select_features(raw,y,tr)
                    assert np.isfinite(x).all()
                    joblib.dump(dict(order=order,scaler=scaler,fit_ids=c.subject_id.iloc[tr].tolist()),folder/(rep+'_transform.joblib'))
                    features[rep+'_lr']=x
                    features[rep+'_adjusted_lr']=np.column_stack([x,controls_x['site_motion_lr']])
                    scores=[]
                    for seed in [1200+fold,2200+fold,3200+fold]:
                        name=rep+'_mlp_seed'+str(seed)
                        model,xt,info=train_neural(x,y,tr,va,fold,name,folder,seed=seed)
                        score=predict(model,xt,te)
                        saved=torch.load(folder/f'fold{fold}_{name}.pt',weights_only=True)
                        replay=MLP(saved['input_features']);replay.load_state_dict(saved['state_dict'])
                        np.testing.assert_allclose(predict(replay,xt,te),score,rtol=1e-6,atol=1e-7)
                        scores.append(score);training.append(dict(repeat=repeat,fold=fold,model=name,**info))
                    features[rep+'_mlp_ens']=np.mean(scores,axis=0)
                fd_cut=float(c.mean_fd.iloc[tr].median())
                for name,x in features.items():
                    if name.endswith('mlp_ens'):score=x
                    else:
                        models=[];aucs=[]
                        for cc in CS:
                            model=LogisticRegression(C=cc,class_weight='balanced',solver='liblinear',max_iter=5000,random_state=42).fit(x[tr],y[tr])
                            aucs.append(float(roc_auc_score(y[va],model.decision_function(x[va]))));models.append(model)
                        best=next(i for i,v in enumerate(aucs) if v>=max(aucs)-1e-12)
                        searches.extend(dict(repeat=repeat,fold=fold,model=name,C=cc,validation_auc=v,selected=i==best) for i,(cc,v) in enumerate(zip(CS,aucs)))
                        model=models[best];joblib.dump(model,folder/(name+'.joblib'));score=model.decision_function(x[te])
                        np.testing.assert_allclose(joblib.load(folder/(name+'.joblib')).decision_function(x[te]),score,rtol=1e-8,atol=1e-8)
                    predictions.extend(dict(repeat=repeat,fold=fold,model=name,subject_id=c.subject_id.iloc[i],y=int(y[i]),score=float(v),site=c.site.iloc[i],mean_fd=c.mean_fd.iloc[i],train_fd_median=fd_cut) for i,v in zip(te,score))
                audits.append(dict(repeat=repeat,fold=fold,residual=residual,prediction_replay_passed=True))
                for name,rows in [('predictions',predictions),('linear_search',searches),('training',training),('fold_audit',audits)]:pd.DataFrame(rows).to_csv(out/(name+'.csv'),index=False)
                status('fold_complete',repeat=repeat,fold=fold,completed_folds=len(audits));print(tag,'complete; test metrics withheld',flush=True)
                del tx,features
        summarize(out,c);status('complete_replay_checked',completed_folds=15)
        print('COMPLETE',out,flush=True)
    except BaseException as e:
        status('failed',error=repr(e));traceback.print_exc();raise

if __name__=='__main__':main()
