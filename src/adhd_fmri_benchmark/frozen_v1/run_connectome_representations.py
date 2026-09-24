"""Fixed representation-by-classifier comparison on audited378, train-only tangent reference."""
from pathlib import Path
import sys
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE/'vendor/connectome0121'))
import argparse
import json
import time
import warnings
from datetime import datetime
import joblib
import numpy as np
import pandas as pd
import torch
import nilearn
from nilearn.connectome import ConnectivityMeasure,sym_matrix_to_vec
from sklearn.covariance import LedoitWolf
from sklearn.feature_selection import f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score,average_precision_score,balanced_accuracy_score
from threadpoolctl import threadpool_limits
from run_tcn_fc_completion import load_data
from run_functional_fusion import train_neural,predict,save_json,digest
from run_connectivity import rank_auc

REPS=['pearson','shrinkage','tangent']
CLASSIFIERS=['lr','linear_svm','mlp_ens']
CS=[.01,.1,1.]

def select_features(x,y,tr,k=1000):
    f,_=f_classif(x[tr],y[tr]);f=np.nan_to_num(f,nan=-np.inf,posinf=np.finfo(float).max,neginf=-np.inf)
    order=np.lexsort((np.arange(x.shape[1]),-f))[:k]
    scaler=StandardScaler().fit(x[tr][:,order])
    return scaler.transform(x[:,order]).astype(np.float32),order,scaler

def tangent_measure():
    return ConnectivityMeasure(cov_estimator=LedoitWolf(store_precision=False),kind='tangent',
        vectorize=True,discard_diagonal=True,standardize=False)

def tangent_features(data,tr):
    measure=tangent_measure()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always');measure.fit([data[i] for i in tr])
    reference=measure.mean_.copy();white=measure.whitening_.copy()
    x=measure.transform(data).astype(np.float32)
    np.testing.assert_array_equal(measure.mean_,reference);np.testing.assert_array_equal(measure.whitening_,white)
    assert np.isfinite(x).all() and np.linalg.eigvalsh(reference).min()>0
    return x,measure,[str(w.message) for w in caught]

def evaluate(out):
    p=pd.read_csv(out/'predictions.csv');rows=[]
    assert len(p)==378*9 and not p.duplicated(['model','subject_id']).any()
    for (fold,name),g in p.groupby(['fold','model']):
        threshold=.5 if name.endswith('mlp_ens') else 0.
        rows.append(dict(fold=int(fold),model=name,auc=roc_auc_score(g.y,g.score),ap=average_precision_score(g.y,g.score),balanced_accuracy=balanced_accuracy_score(g.y,g.score>=threshold)))
    fm=pd.DataFrame(rows);fm.to_csv(out/'fold_metrics.csv',index=False)
    summary=fm.groupby('model').agg(mean_auc=('auc','mean'),sd_auc=('auc','std'),mean_ap=('ap','mean'),mean_balanced_accuracy=('balanced_accuracy','mean')).reset_index()
    summary.to_csv(out/'summary.csv',index=False)
    wide=p.pivot(index=['fold','subject_id','y'],columns='model',values='score').reset_index()
    groups=[g.reset_index(drop=True) for _,g in wide.groupby('fold')];rng=np.random.default_rng(2026)
    resamples=[[np.concatenate([rng.choice(np.flatnonzero(g.y.to_numpy()==c),(g.y==c).sum(),replace=True) for c in [0,1]]) for g in groups] for _ in range(1000)]
    comparisons=[]
    for classifier in CLASSIFIERS:
        b='pearson_'+classifier
        for rep in ['shrinkage','tangent']:
            a=rep+'_'+classifier
            point=np.mean([rank_auc(g.y.to_numpy(),g[a].to_numpy())-rank_auc(g.y.to_numpy(),g[b].to_numpy()) for g in groups])
            draws=[np.mean([rank_auc(g.y.to_numpy()[ix],g[a].to_numpy()[ix])-rank_auc(g.y.to_numpy()[ix],g[b].to_numpy()[ix]) for g,ix in zip(groups,r)]) for r in resamples]
            comparisons.append(dict(candidate=a,reference=b,delta_mean_auc=point,ci_low=np.quantile(draws,.025),ci_high=np.quantile(draws,.975),primary=a=='tangent_lr',caveat='Fixed OOF conditional fold/label paired bootstrap; no refitting, split uncertainty or multiplicity correction.'))
    pd.DataFrame(comparisons).to_csv(out/'paired_bootstrap.csv',index=False)
    return summary

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--smoke',action='store_true');args=parser.parse_args()
    torch.set_num_threads(4)
    assert nilearn.__version__=='0.12.1'
    out=BASE/'runs'/datetime.now().strftime('connectome_representations_%Y%m%d_%H%M%S');out.mkdir()
    protocol=dict(status='preflight',smoke_only=args.smoke,n=378,representations=REPS,classifiers=CLASSIFIERS,
        primary='tangent_lr minus pearson_lr, mean fold AUC',
        representation_details='Pearson raw correlations without Fisher z; LedoitWolf covariances; affine-invariant geometric-mean tangent of same LedoitWolf estimator. All discard diagonal, same89676 lower-triangle entries.',
        standardization='Existing full-scan within-person ROI z-score cache at1Hz; no new resampling. Time points are autocorrelated and not independent observations.',
        tangent_reference='Fit on201 training subjects only, never validation/test; transform does not update mean or whitening.',
        feature_selection='ANOVA top1000 fit on each201 training subjects separately per representation, standardize selected features on same training only.',
        linear='LR and LinearSVC, balanced weights,C in [.01,.1,1.], choose validation decision-AUC, earliest near tie; no refit on validation.',
        neural='Same64/16 MLP;3 seeds1200+fold,2200+fold,3200+fold; all retained equally;epochs80max,patience12,lr.001,batch16,weight_decay.01.',
        scores='Native decision margins for linear models, no probability calibration or score flipping. Probabilities for MLP. No pooled across-fold margin AUC.',
        fit_counts=dict(linear_candidates=54,neural_fits=27,reported_model_folds=27),
        exclusions='Same clean378,13 label conflicts excluded; no age/sex/site/QC/structural covariates as predictors.',
        device='CPU',threads=4,nilearn=nilearn.__version__,torch=torch.__version__,
        sources=['https://nilearn.github.io/stable/modules/generated/nilearn.connectome.ConnectivityMeasure.html','https://scikit-learn.org/stable/modules/generated/sklearn.covariance.LedoitWolf.html'],
        caveat='Adaptive internal development,not external/untouched validation;historical0.622 not directly paired.')
    save_json(out/'protocol.json',protocol)
    for name in ['run_connectome_representations.py','run_functional_fusion.py']:(out/name).write_bytes((BASE/name).read_bytes())
    cohort,splits,series,fc,edges,folds=load_data();del fc,edges
    y=cohort.label.to_numpy(np.int64)
    data=[np.asarray(series.base.data[series.base.offsets[i]:series.base.offsets[i+1]],dtype=np.float64) for i in series.indices]
    del series
    cohort.to_csv(out/'cohort.csv',index=False);splits.to_csv(out/'splits.csv',index=False)
    protocol.update(status='running',split_sha256=digest(out/'splits.csv'),cohort_sha256=digest(out/'cohort.csv'))
    save_json(out/'protocol.json',protocol);started=time.monotonic()
    with threadpool_limits(limits=4):
        if args.smoke:
            small=[data[i][:128,:16] for i in folds[0][1][:20]]
            x,measure,notes=tangent_features(small,np.arange(8))
            assert x.shape==(20,120)
            save_json(out/'smoke.json',dict(status='synthetic_size_pipeline_only',shape=list(x.shape),warnings=notes))
            print('SMOKE',out,flush=True);return
        plain=[];shrunk=[];shrinkage=[]
        for i,d in enumerate(data):
            plain.append(sym_matrix_to_vec(np.corrcoef(d,rowvar=False),discard_diagonal=True).astype(np.float32))
            estimator=LedoitWolf(store_precision=False).fit(d)
            shrunk.append(sym_matrix_to_vec(estimator.covariance_,discard_diagonal=True).astype(np.float32))
            shrinkage.append(dict(subject_id=cohort.subject_id.iloc[i],shrinkage=float(estimator.shrinkage_),n_frames=len(d)))
            if (i+1)%100==0:print('COVARIANCES',i+1,flush=True)
        features={'pearson':np.stack(plain),'shrinkage':np.stack(shrunk)};del plain,shrunk
        assert all(a.shape==(378,89676) and np.isfinite(a).all() for a in features.values())
        np.savez_compressed(out/'subject_features.npz',subject_id=cohort.subject_id.to_numpy(dtype=str),**features)
        pd.DataFrame(shrinkage).to_csv(out/'shrinkage_strength.csv',index=False)
        preds=[];vals=[];candidates=[];seed_rows=[];training=[];tangent_info=[]
        for fold,tr,va,te in folds:
            print('FOLD',fold,'fitting tangent reference on201 training subjects',flush=True)
            t=time.monotonic();tx,measure,notes=tangent_features(data,tr)
            joblib.dump(dict(measure=measure,fit_ids=cohort.subject_id.iloc[tr].tolist()),out/f'fold{fold}_tangent.joblib')
            np.save(out/f'fold{fold}_tangent.npy',tx)
            tangent_info.append(dict(fold=fold,seconds=time.monotonic()-t,warnings=notes,reference_min_eigenvalue=float(np.linalg.eigvalsh(measure.mean_).min())))
            save_json(out/'tangent_info.json',tangent_info)
            for rep in REPS:
                x,order,scaler=select_features(tx if rep=='tangent' else features[rep],y,tr)
                joblib.dump(dict(order=order,scaler=scaler,fit_ids=cohort.subject_id.iloc[tr].tolist()),out/f'fold{fold}_{rep}_transform.joblib')
                for kind in ['lr','linear_svm']:
                    name=rep+'_'+kind;models=[];search=[]
                    for c in CS:
                        model=LogisticRegression(C=c,class_weight='balanced',solver='liblinear',max_iter=5000,random_state=42) if kind=='lr' else LinearSVC(C=c,class_weight='balanced',dual=True,max_iter=20000,random_state=42)
                        with warnings.catch_warnings(record=True) as caught:
                            warnings.simplefilter('always');model.fit(x[tr],y[tr])
                        v=model.decision_function(x[va]);auc=float(roc_auc_score(y[va],v))
                        search.append(dict(fold=fold,model=name,C=c,validation_auc=auc,warnings='; '.join(str(w.message) for w in caught)))
                        models.append(model);joblib.dump(model,out/f'fold{fold}_{name}_C{c}.joblib')
                    best=next(i for i,r in enumerate(search) if r['validation_auc']>=max(v['validation_auc'] for v in search)-1e-12)
                    candidates.extend(dict(**r,selected=i==best) for i,r in enumerate(search))
                    model=models[best]
                    for idx,rows in [(va,vals),(te,preds)]:rows.extend(dict(fold=fold,model=name,subject_id=cohort.subject_id.iloc[i],y=int(y[i]),score=float(p),score_type='native_margin') for i,p in zip(idx,model.decision_function(x[idx])))
                vp=[];tp=[];name=rep+'_mlp_ens'
                for seed in [1200+fold,2200+fold,3200+fold]:
                    model,xt,info=train_neural(x,y,tr,va,fold,name+'_seed'+str(seed),out,seed=seed)
                    v=predict(model,xt,va);p=predict(model,xt,te);vp.append(v);tp.append(p)
                    training.append(dict(fold=fold,model=name,seed=seed,**info))
                    for role,idx,values in [('validation',va,v),('test',te,p)]:seed_rows.extend(dict(fold=fold,model=name,seed=seed,role=role,subject_id=cohort.subject_id.iloc[i],y=int(y[i]),score=float(s)) for i,s in zip(idx,values))
                for idx,values,rows in [(va,np.mean(vp,axis=0),vals),(te,np.mean(tp,axis=0),preds)]:rows.extend(dict(fold=fold,model=name,subject_id=cohort.subject_id.iloc[i],y=int(y[i]),score=float(p),score_type='probability') for i,p in zip(idx,values))
                print('FINISHED',fold,rep,'all classifiers; test metrics withheld',flush=True)
                for filename,rows in [('predictions',preds),('validation_predictions',vals),('linear_candidates',candidates),('seed_predictions',seed_rows),('training_summary',training)]:pd.DataFrame(rows).to_csv(out/(filename+'.csv'),index=False)
            del tx
    summary=evaluate(out)
    save_json(out/'complete.json',dict(status='complete_pending_replay',seconds=time.monotonic()-started))
    print(summary.to_string(index=False),flush=True);print('OUTPUT',out,flush=True)

if __name__=='__main__':main()
