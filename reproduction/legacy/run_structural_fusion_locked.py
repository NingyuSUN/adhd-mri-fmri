"""Prespecified QC-locked structural / functional / late-fusion paired analysis.
No modifications to frozen fMRI runs. Resume only hash-verified completed folds.
"""
from pathlib import Path
import sys, json, time, warnings, argparse, traceback
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE/'vendor/connectome0121'))
import numpy as np
import pandas as pd
import joblib, torch
from sklearn.covariance import LedoitWolf
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score,average_precision_score,balanced_accuracy_score,brier_score_loss
from nilearn.connectome import sym_matrix_to_vec
from nilearn.connectome.connectivity_matrices import _geometric_mean
from threadpoolctl import threadpool_limits
from run_functional_fusion import save_json,digest,train_neural,predict,MLP
from run_repeated_connectome import controls
from run_demographic_increment import demographic
from run_connectome_representations import select_features
from refine_tangent_reference import transform
from run_incremental_imaging import choose_alpha,conditional_auc

OUT=BASE/'runs/structural_fusion_locked_20260909'
PARENT=BASE/'runs/demographic_increment_20260908_locked_v2'
QC=BASE/'runs/structural_qc_locked_20260909/qc_lock.json'
VOL=BASE/'runs/structural_features378_20260909/volumes_NOT_TRAINING_READY.npz'
CACHE=BASE/'runs/temporal_cache_20260907_113751'
QC_SHA='e03ad88399837fb5e894c7eae633acc806082a8cd9dfbd9c1a1180c85608ddc4'
CS=[.01,.1,1.,10.]
COHORTS=['primary','warning_free','include_holds']
MODEL_NAMES=['structural_lr','structural_tiv_lr','tiv_lr','full_covariates_lr','full_covariates_tiv_lr',
 'tangent_lr','structural_mlp','tangent_mlp','image_fusion_lr','image_fusion_mlp',
 'full_functional_lr','full_functional_mlp','full_functional_tiv_mlp',
 'full_fusion_lr','full_fusion_mlp','full_fusion_tiv_mlp','full_fusion_structural_mlp']
CONTRASTS=[('full_fusion_mlp','full_functional_mlp'),('full_fusion_lr','full_functional_lr'),
 ('image_fusion_mlp','tangent_mlp'),('image_fusion_lr','tangent_lr'),
 ('full_functional_mlp','full_covariates_lr'),('full_fusion_tiv_mlp','full_functional_tiv_mlp'),
 ('full_fusion_structural_mlp','full_functional_mlp'),('structural_mlp','structural_lr'),
 ('structural_tiv_lr','structural_lr')]
DEPENDENCIES=['run_functional_fusion.py','run_repeated_connectome.py','run_demographic_increment.py',
 'run_connectome_representations.py','refine_tangent_reference.py','run_incremental_imaging.py',
 'vendor/connectome0121/nilearn/connectome/connectivity_matrices.py']

def protocol():
    return dict(qc_sha256=QC_SHA,cohorts=COHORTS,C=CS,alpha=[0,.25,.5,.75,1],models=MODEL_NAMES,
      primary_contrast=list(CONTRASTS[0]),comparisons=CONTRASTS,
      structural='98 region/TIV fractions, not cortical thickness; separate TIV covariate sensitivity',
      splits='Exact saved original repeat/fold/role filtered by fixed QC cohort; no regeneration',
      functional='Refit tangent geometric mean on retained train only; within-subject LedoitWolf; ANOVA top1000 and scaler train only',
      geometry=dict(max_iter=100,tol=1e-8,residual_max=1e-7),
      lr='balanced L2 liblinear, max_iter5000, seed42; validation AUC selects C, ties smaller C',
      mlp=dict(hidden=[64,16],activation='GELU',dropout=[.4,.3],epochs_max=80,patience=12,
       lr=.001,weight_decay=.01,batch=16,clip=1.,seeds='1200+fold,2200+fold,3200+fold; equal ensemble',
       selection='validation-only early stopping, fixed existing training function; no architecture grid'),
      fusion='validation-only convex weights; ties prefer less added modality; sequential covariate+functional then structural. Same validation reused, exploratory.',
      sensitivity='warning_free excludes all warnings and holds; include_holds retains unresolved holds but excludes 3 failures. Never select cohort by scores.',
      metrics='mean of fold AUC then mean across5 repeats; within-site pair-weighted AUC; AP, BA at0.5 and Brier descriptive only; repeat range is NOT CI',
      caveat='Adaptive reused internal cohort, no external validation or clinical-risk calibration; sampled assistant QC not expert anatomical acceptance.',
      input_hashes={str(p.relative_to(BASE)):digest(p) for p in [QC,VOL,PARENT/'cohort.csv',PARENT/'splits.csv',CACHE/'verification.json']},
      code_hashes={name:digest(BASE/name) for name in [Path(__file__).name]+DEPENDENCIES})

def prepare():
    assert digest(QC)==QC_SHA
    q=json.loads(QC.read_text());assert q['reviewed']==378 and q['dense_reviewed']==76
    assert digest(VOL)==q['feature_sha256']
    c=pd.read_csv(PARENT/'cohort.csv');sp=pd.read_csv(PARENT/'splits.csv')
    assert c.subject_id.is_unique and len(c)==378 and not c[['label_conflict','age_conflict','sex_conflict']].any().any()
    assert set(c.subject_id)=={r['subject_id'] for r in q['subjects']}
    assert not sp.duplicated(['repeat','fold','subject_id']).any()
    spec=protocol()
    if (OUT/'protocol.json').exists():
        assert json.loads((OUT/'protocol.json').read_text())==json.loads(json.dumps(spec)), 'Frozen executable config changed'
    else:
        OUT.mkdir(exist_ok=False);save_json(OUT/'protocol.json',spec)
        for name in [Path(__file__).name]+DEPENDENCIES:
            dest=OUT/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((BASE/name).read_bytes())
        for name in COHORTS:
            folder=OUT/name;folder.mkdir()
            cc=c[c.subject_id.isin(q['cohorts'][name])].copy().reset_index(drop=True)
            ss=sp[sp.subject_id.isin(cc.subject_id)].copy()
            assert len(cc)==len(q['cohorts'][name])
            for (r,f),g in ss.groupby(['repeat','fold']):
                assert len(g)==len(cc) and g.subject_id.is_unique
                assert set(g.role)=={'train','validation','test'}
                for role,h in g.groupby('role'):assert set(h.label)=={0,1}
            assert ss[ss.role.eq('test')].groupby(['repeat','subject_id']).size().eq(1).all()
            cc.to_csv(folder/'cohort.csv',index=False);ss.to_csv(folder/'splits.csv',index=False)
        save_json(OUT/'status.json',dict(status='prepared',completed_folds=0,total_folds=45))
    return c

def covariance_cache(c):
    dest=OUT/'covariances.npy';meta=OUT/'covariances.json'
    if meta.exists():
        m=json.loads(meta.read_text());assert digest(dest)==m['sha256']
        assert m['ids']==c.subject_id.tolist()
        return np.load(dest,mmap_mode='r')
    vm=json.loads((CACHE/'verification.json').read_text())
    assert digest(CACHE/'timeseries.npz')==vm['cache_sha256']
    assert vm['effective_sample_interval_seconds']==1.
    z=np.load(CACHE/'timeseries.npz',allow_pickle=False)
    ids=z['subject_id'].astype(str);ix={s:i for i,s in enumerate(ids)};assert len(ix)==len(ids)
    data=z['data'];offset=z['offsets'];assert data.shape[1]==424 and offset[-1]==len(data)
    cov=[]
    for n,sid in enumerate(c.subject_id):
        i=ix[sid];d=np.asarray(data[offset[i]:offset[i+1]],dtype=np.float64)
        assert d.ndim==2 and np.isfinite(d).all()
        cov.append(LedoitWolf(store_precision=False).fit(d).covariance_)
        if n%50==0:print('COVARIANCE',n,'/378',flush=True)
    z.close();arr=np.asarray(cov);assert arr.shape==(378,424,424)
    np.save(dest,arr);save_json(meta,dict(sha256=digest(dest),ids=c.subject_id.tolist(),source_sha256=vm['cache_sha256'],scope='within-person only; no group fit'))
    return np.load(dest,mmap_mode='r')

def fit_lr(name,x,y,tr,va,te,folder,search):
    models=[];aucs=[]
    for cc in CS:
        model=LogisticRegression(C=cc,class_weight='balanced',solver='liblinear',max_iter=5000,random_state=42).fit(x[tr],y[tr])
        models.append(model);aucs.append(float(roc_auc_score(y[va],model.predict_proba(x[va])[:,1])))
        assert model.n_iter_.max()<5000
    best=next(i for i,v in enumerate(aucs) if v>=max(aucs)-1e-12)
    search.extend(dict(model=name,C=cc,validation_auc=a,selected=i==best) for i,(cc,a) in enumerate(zip(CS,aucs)))
    joblib.dump(models[best],folder/(name+'.joblib'));replay=joblib.load(folder/(name+'.joblib'))
    result={}
    for role,ix in [('validation',va),('test',te)]:
        result[role]=models[best].predict_proba(x[ix])[:,1]
        np.testing.assert_allclose(replay.predict_proba(x[ix])[:,1],result[role],atol=1e-10)
    return result

def fit_mlp(name,x,y,tr,va,te,fold,folder,training):
    scores={'validation':[],'test':[]}
    for seed in [1200+fold,2200+fold,3200+fold]:
        tag=name+'_seed'+str(seed);model,xt,info=train_neural(x,y,tr,va,fold,tag,folder,seed=seed)
        saved=torch.load(folder/f'fold{fold}_{tag}.pt',weights_only=True)
        replay=MLP(saved['input_features']);replay.load_state_dict(saved['state_dict'])
        for role,ix in [('validation',va),('test',te)]:
            p=predict(model,xt,ix)
            np.testing.assert_allclose(predict(replay,xt,ix),p,rtol=1e-6,atol=1e-7)
            scores[role].append(p)
        training.append(dict(model=tag,seed=seed,**info))
    return {role:np.mean(v,axis=0) for role,v in scores.items()}

def blend(name,base,added,scores,yval,selection):
    alpha,aucs=choose_alpha(yval,scores[base]['validation'],scores[added]['validation'])
    selection.extend(dict(model=name,base=base,added=added,alpha=a,validation_auc=v,selected=a==alpha) for a,v in zip([0,.25,.5,.75,1],aucs))
    scores[name]={role:(1-alpha)*scores[base][role]+alpha*scores[added][role] for role in ['validation','test']}

def run_fold(c,sp,vol,tiv,cov,repeat,fold,folder):
    folder.mkdir(exist_ok=True);lookup={sid:i for i,sid in enumerate(c.subject_id)}
    group=sp[sp.repeat.eq(repeat)&sp.fold.eq(fold)]
    tr,va,te=[np.array([lookup[s] for s in group[group.role.eq(role)].subject_id]) for role in ['train','validation','test']]
    assert not(set(tr)&set(va) or set(tr)&set(te) or set(va)&set(te))
    assert sorted(np.r_[tr,va,te])==list(range(len(c)))
    y=c.label.to_numpy(np.int64);search=[];selection=[];training=[];scores={}
    print(folder.parent.name,repeat,fold,'geometry',len(tr),len(va),len(te),flush=True)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always');mean=_geometric_mean(cov[tr],max_iter=100,tol=1e-8)
    white,logs=transform(cov,mean);residual=float(np.linalg.norm(logs[tr].mean(axis=0))/mean.size)
    assert residual<1e-7,f'Geometry residual {residual}'
    raw=sym_matrix_to_vec(logs,discard_diagonal=True).astype(np.float32);del logs
    tx,order,tscale=select_features(raw,y,tr);del raw
    sc=StandardScaler().fit(vol[tr]);sx=sc.transform(vol).astype(np.float32)
    tsc=StandardScaler().fit(tiv[tr,None]);tv=tsc.transform(tiv[:,None])
    ctrl,ctrlfit=controls(c,tr);dx,dfit=demographic(c,tr);full=np.c_[ctrl['site_motion_lr'],dx]
    joblib.dump(dict(mean=mean,white=white,order=order,tangent_scaler=tscale,structural_scaler=sc,tiv_scaler=tsc,
      controls=ctrlfit,demographic=dfit,fit_ids=c.subject_id.iloc[tr].tolist()),folder/'transforms.joblib')
    for name,x in [('structural_lr',sx),('structural_tiv_lr',np.c_[sx,tv]),('tiv_lr',tv),
       ('full_covariates_lr',full),('full_covariates_tiv_lr',np.c_[full,tv]),('tangent_lr',tx)]:
        scores[name]=fit_lr(name,x,y,tr,va,te,folder,search)
    print(folder.parent.name,repeat,fold,'neural',flush=True)
    scores['structural_mlp']=fit_mlp('structural_mlp',sx,y,tr,va,te,fold,folder,training)
    scores['tangent_mlp']=fit_mlp('tangent_mlp',tx,y,tr,va,te,fold,folder,training)
    for name,base,added in [
      ('image_fusion_lr','tangent_lr','structural_lr'),('image_fusion_mlp','tangent_mlp','structural_lr'),
      ('full_functional_lr','full_covariates_lr','tangent_lr'),('full_functional_mlp','full_covariates_lr','tangent_mlp'),
      ('full_functional_tiv_mlp','full_covariates_tiv_lr','tangent_mlp'),
      ('full_fusion_lr','full_functional_lr','structural_lr'),('full_fusion_mlp','full_functional_mlp','structural_lr'),
      ('full_fusion_tiv_mlp','full_functional_tiv_mlp','structural_lr'),
      ('full_fusion_structural_mlp','full_functional_mlp','structural_mlp')]:
        blend(name,base,added,scores,y[va],selection)
    assert set(scores)==set(MODEL_NAMES)
    for role,ix in [('validation',va),('test',te)]:
        rows=[]
        for name,v in scores.items():
            p=v[role];assert np.isfinite(p).all() and ((p>=0)&(p<=1)).all()
            rows.extend(dict(repeat=repeat,fold=fold,model=name,subject_id=c.subject_id.iloc[i],
               site=c.site.iloc[i],y=int(y[i]),score=float(s)) for i,s in zip(ix,p))
        pd.DataFrame(rows).to_csv(folder/(role+'.csv'),index=False)
    pd.DataFrame(search).to_csv(folder/'C_search.csv',index=False)
    pd.DataFrame(selection).to_csv(folder/'selection.csv',index=False)
    pd.DataFrame(training).to_csv(folder/'training.csv',index=False)
    save_json(folder/'audit.json',dict(residual=residual,geometry_warnings=[str(w.message) for w in caught],
      train_ids=c.subject_id.iloc[tr].tolist(),validation_ids=c.subject_id.iloc[va].tolist(),test_ids=c.subject_id.iloc[te].tolist(),
      checkpoint_replay_passed=True,diagnosis_used_for_qc=False,roles_preserved=True))
    files={p.name:digest(p) for p in folder.iterdir() if p.is_file() and p.name!='complete.json'}
    save_json(folder/'complete.json',dict(status='complete_replay_checked',files=files,protocol_sha256=digest(OUT/'protocol.json')))

def summarize():
    for cohort in COHORTS:
        folder=OUT/cohort;c=pd.read_csv(folder/'cohort.csv')
        p=pd.concat([pd.read_csv(folder/f'repeat{r}_fold{f}/test.csv') for r in range(1,6) for f in range(1,4)])
        assert len(p)==len(c)*5*len(MODEL_NAMES) and not p.duplicated(['repeat','model','subject_id']).any()
        p.to_csv(folder/'predictions.csv',index=False)
        rows=[]
        for (r,f,m),g in p.groupby(['repeat','fold','model']):
            rows.append(dict(repeat=r,fold=f,model=m,n=len(g),auc=roc_auc_score(g.y,g.score),
              within_site_auc=conditional_auc(g),ap=average_precision_score(g.y,g.score),
              balanced_accuracy=balanced_accuracy_score(g.y,g.score>=.5),brier=brier_score_loss(g.y,g.score)))
        fm=pd.DataFrame(rows);fm.to_csv(folder/'fold_metrics.csv',index=False)
        rm=fm.groupby(['repeat','model'])[['auc','within_site_auc','ap','balanced_accuracy','brier']].mean().reset_index()
        rm.to_csv(folder/'repeat_metrics.csv',index=False)
        summary=rm.groupby('model').agg(mean_auc=('auc','mean'),min_repeat_auc=('auc','min'),max_repeat_auc=('auc','max'),
          within_site_auc=('within_site_auc','mean'),mean_ap=('ap','mean'),mean_brier=('brier','mean'))
        summary.to_csv(folder/'summary.csv')
        deltas=[]
        for metric in ['auc','within_site_auc']:
            wide=rm.pivot(index='repeat',columns='model',values=metric)
            for a,b in CONTRASTS:
                d=wide[a]-wide[b];deltas.append(dict(metric=metric,candidate=a,reference=b,mean_delta=d.mean(),
                  min_delta=d.min(),max_delta=d.max(),positive_repeats=int((d>1e-12).sum()),total_repeats=5))
        pd.DataFrame(deltas).to_csv(folder/'paired_deltas.csv',index=False)
    save_json(OUT/'status.json',dict(status='complete_replay_checked',completed_folds=45,total_folds=45,models_per_fold=len(MODEL_NAMES)))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepare-only',action='store_true');args=ap.parse_args()
    c0=prepare()
    if args.prepare_only:print('PREPARED',OUT,flush=True);return
    try:
        torch.set_num_threads(4)
        with threadpool_limits(limits=4):
            cov0=covariance_cache(c0)
            z=np.load(VOL,allow_pickle=False);vi={s:i for i,s in enumerate(z['subject_id'].astype(str))}
            ci={s:i for i,s in enumerate(c0.subject_id)};completed=0
            for name in COHORTS:
                folder=OUT/name;c=pd.read_csv(folder/'cohort.csv');sp=pd.read_csv(folder/'splits.csv')
                cov=np.asarray(cov0[[ci[s] for s in c.subject_id]])
                ix=[vi[s] for s in c.subject_id];vol=z['volume_fractions'][ix];tiv=z['total_intracranial_mm3'][ix]
                assert vol.shape==(len(c),98) and np.isfinite(vol).all()
                for r in range(1,6):
                    for f in range(1,4):
                        dest=folder/f'repeat{r}_fold{f}'
                        if (dest/'complete.json').exists():
                            meta=json.loads((dest/'complete.json').read_text())
                            assert meta['protocol_sha256']==digest(OUT/'protocol.json')
                            for file,h in meta['files'].items():assert digest(dest/file)==h
                        else:
                            save_json(OUT/'status.json',dict(status='running',cohort=name,repeat=r,fold=f,completed_folds=completed,total_folds=45,updated=time.strftime('%Y-%m-%d %H:%M:%S')))
                            run_fold(c,sp,vol,tiv,cov,r,f,dest)
                        completed+=1;print('FOLD COMPLETE',completed,'/45; test metrics withheld until all planned fits complete',flush=True)
            summarize()
        print('COMPLETE',OUT,flush=True)
    except BaseException as e:
        save_json(OUT/'status.json',dict(status='failed',error=repr(e)));traceback.print_exc();raise
if __name__=='__main__':main()

