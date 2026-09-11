"""Locked demographic sensitivity analysis using previously replayed imaging scores."""
from pathlib import Path
import json,sys,traceback
import numpy as np
import pandas as pd
import joblib
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from threadpoolctl import threadpool_limits
from run_repeated_connectome import partitions,controls
from run_incremental_imaging import choose_alpha,ALPHAS,conditional_auc
from run_functional_fusion import save_json,digest
BASE=Path(__file__).resolve().parent
PARENT=BASE/'runs/incremental_imaging_20260908_locked'
OUT=BASE/'runs/demographic_increment_20260908_locked_v2'
CS=[.01,.1,1.]

def demographic(c,tr):
    raw=c[['participant_age','participant_sex_male']].to_numpy(dtype=float,copy=True)
    raw[~np.isfinite(raw)]=np.nan
    imp=SimpleImputer(strategy='median',keep_empty_features=True).fit(raw[tr])
    x=np.column_stack([imp.transform(raw),np.isnan(raw).astype(float)])
    scale=StandardScaler().fit(x[tr])
    return scale.transform(x),dict(imputer=imp,scaler=scale,fit_ids=c.subject_id.iloc[tr].tolist())

def main():
    OUT.mkdir(exist_ok=False)
    try:
        save_json(OUT/'status.json',dict(status='running'))
        assert json.loads((PARENT/'status.json').read_text())['status']=='complete_replay_checked'
        c=pd.read_csv(PARENT/'cohort.csv');y=c.label.to_numpy(dtype=int);parts=list(partitions(c))
        assert not c[['age_conflict','sex_conflict','label_conflict']].any().any()
        assert c.participant_sex_male.dropna().isin([0,1]).all()
        assert c.participant_age.dropna().between(0,100).all()
        provenance=[]
        for key,columns in [('participant_age',['structural_age','fmri_age','roi_age']),('participant_sex_male',['structural_sex_male','fmri_sex_male','roi_sex_male'])]:
            assert c[key].notna().all()
            for col in columns:
                observed=c[col].notna()
                np.testing.assert_allclose(c.loc[observed,key],c.loc[observed,col])
                provenance.append(dict(primary=key,comparison=col,missing_comparison=int((~observed).sum()),observed_values_agree=True))
        save_json(OUT/'demographic_provenance.json',provenance)
        save_json(OUT/'protocol.json',dict(parent=str(PARENT),primary='fusion_tangent_mlp minus full_covariates_lr mean fold AUC',secondary='LR fusion; within-site pair-weighted AUC; demographics-only and previous site-motion controls',folds=15,n=378,C=CS,alphas=ALPHAS,demographics=['participant_age','participant_sex_male'],preprocessing='train-only median imputation, missing flags and scaling; site/motion same previous controls',selection='validation-only C and alpha; ties lower C/alpha; no test-based adaptation',caveat='Adaptive reused internal cohort and validation; linear covariate control incomplete, no causal/clinical/external validation claim; uncalibrated probabilities',source_sha256=digest(Path(__file__)),split_sha256=digest(PARENT/'splits.csv')))
        (OUT/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
        for name in ['cohort.csv','splits.csv']:(OUT/name).write_bytes((PARENT/name).read_bytes())
        old=pd.read_csv(PARENT/'predictions.csv');preds=[];sels=[];search=[];audits=[]
        with threadpool_limits(limits=4):
            for repeat,fold,tr,va,te in parts:
                folder=OUT/f'repeat{repeat}_fold{fold}';folder.mkdir()
                dx,fit=demographic(c,tr);ctrl,ctrlfit=controls(c,tr)
                changed=c.copy();changed.loc[te,'participant_age']=99
                dd,_=demographic(changed,tr);np.testing.assert_array_equal(dx[tr],dd[tr])
                joblib.dump(dict(demographic=fit,controls=ctrlfit),folder/'preprocessing.joblib')
                test=old[old.repeat.eq(repeat)&old.fold.eq(fold)].pivot(index='subject_id',columns='model',values='score').loc[c.subject_id.iloc[te]]
                validation=pd.read_csv(PARENT/f'repeat{repeat}_fold{fold}_validation.csv').pivot(index='subject_id',columns='model',values='score').loc[c.subject_id.iloc[va]]
                scores={role:{'site_motion_lr':w.site_motion_lr.to_numpy()} for role,w in [('validation',validation),('test',test)]}
                for name,x in [('demographic_lr',dx),('full_covariates_lr',np.column_stack([ctrl['site_motion_lr'],dx]))]:
                    models=[];auc=[]
                    for cc in CS:
                        model=LogisticRegression(C=cc,class_weight='balanced',solver='liblinear',max_iter=5000,random_state=42).fit(x[tr],y[tr])
                        models.append(model);auc.append(roc_auc_score(y[va],model.predict_proba(x[va])[:,1]))
                    best=next(i for i,v in enumerate(auc) if v>=max(auc)-1e-12)
                    search.extend(dict(repeat=repeat,fold=fold,model=name,C=cc,validation_auc=v,selected=i==best) for i,(cc,v) in enumerate(zip(CS,auc)))
                    joblib.dump(models[best],folder/(name+'.joblib'))
                    for role,ix in [('validation',va),('test',te)]:
                        scores[role][name]=models[best].predict_proba(x[ix])[:,1]
                        np.testing.assert_allclose(joblib.load(folder/(name+'.joblib')).predict_proba(x[ix])[:,1],scores[role][name])
                for image in ['tangent_lr','tangent_mlp']:
                    alpha,aucs=choose_alpha(y[va],scores['validation']['full_covariates_lr'],validation[image].to_numpy())
                    sels.extend(dict(repeat=repeat,fold=fold,image_model=image,alpha=a,validation_auc=v,selected=a==alpha) for a,v in zip(ALPHAS,aucs))
                    for role,w in [('validation',validation),('test',test)]:scores[role]['fusion_'+image]=(1-alpha)*scores[role]['full_covariates_lr']+alpha*w[image].to_numpy()
                    # Independently recompute the selected alpha from saved validation inputs.
                    manual=[roc_auc_score(y[va],(1-a)*scores['validation']['full_covariates_lr']+a*validation[image]) for a in ALPHAS]
                    assert alpha==next(a for a,v in zip(ALPHAS,manual) if v>=max(manual)-1e-12)
                for role,ix in [('validation',va),('test',te)]:
                    rows=[dict(repeat=repeat,fold=fold,model=name,subject_id=c.subject_id.iloc[i],site=c.site.iloc[i],y=int(y[i]),score=float(v)) for name,values in scores[role].items() for i,v in zip(ix,values)]
                    if role=='test':preds.extend(rows)
                    else:pd.DataFrame(rows).to_csv(folder/'validation.csv',index=False)
                audits.append(dict(repeat=repeat,fold=fold,train_only_demographic_test=True,checkpoint_replay=True))
                for name,rows in [('predictions',preds),('selection',sels),('C_search',search),('audit',audits)]:pd.DataFrame(rows).to_csv(OUT/(name+'.csv'),index=False)
                print('FOLD COMPLETE',repeat,fold,flush=True)
        p=pd.DataFrame(preds);assert len(p)==9450 and not p.duplicated(['repeat','model','subject_id']).any()
        fm=pd.DataFrame([dict(repeat=r,fold=f,model=m,auc=roc_auc_score(g.y,g.score),within_site_auc=conditional_auc(g)) for (r,f,m),g in p.groupby(['repeat','fold','model'])]);fm.to_csv(OUT/'fold_metrics.csv',index=False)
        rm=fm.groupby(['repeat','model'])[['auc','within_site_auc']].mean().reset_index();rm.to_csv(OUT/'repeat_metrics.csv',index=False)
        rm.groupby('model').agg(mean_auc=('auc','mean'),min_auc=('auc','min'),max_auc=('auc','max'),within_site_auc=('within_site_auc','mean')).to_csv(OUT/'summary.csv')
        deltas=[]
        for metric in ['auc','within_site_auc']:
            w=rm.pivot(index='repeat',columns='model',values=metric)
            for a,b in [('full_covariates_lr','site_motion_lr'),('fusion_tangent_lr','full_covariates_lr'),('fusion_tangent_mlp','full_covariates_lr')]:
                d=w[a]-w[b];deltas.append(dict(metric=metric,candidate=a,reference=b,mean_delta=d.mean(),min_delta=d.min(),max_delta=d.max(),positive=int((d>1e-12).sum()),negative=int((d< -1e-12).sum()),total=5))
        pd.DataFrame(deltas).to_csv(OUT/'paired_deltas.csv',index=False)
        sel=pd.DataFrame(sels);sel[sel.selected].groupby(['image_model','alpha']).size().rename('folds').to_csv(OUT/'alpha_counts.csv')
        save_json(OUT/'status.json',dict(status='complete_replay_checked',completed_folds=15));print('COMPLETE',OUT,flush=True)
    except BaseException as e:save_json(OUT/'status.json',dict(status='failed',error=repr(e)));raise

if __name__=='__main__':main()
