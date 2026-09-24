"""Complete the teaching deck's TCN/FC experiment on the audited paired cohort."""
import argparse
import json
import time
from datetime import datetime
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import torch
from torch import nn
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score,average_precision_score,brier_score_loss,confusion_matrix,roc_curve
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from threadpoolctl import threadpool_limits
from temporal_models import Series,TemporalNet,predict_subjects
from run_temporal import fit
from run_functional_fusion import BASE,FEATURES,save_json,digest,make_splits
from run_connectivity import rank_auc

REFERENCE=BASE/'runs/functional_fusion_20260907_124543'
CACHE=BASE/'runs/temporal_cache_20260907_113751'
MODELS=['fc_rbf','tcn','tcn_fc','late_tcn_rbf','late_dual_rbf']
ALPHAS=[0.,.25,.5,.75,1.]

class MappedSeries:
    def __init__(self,base,indices):
        self.base=base;self.indices=np.asarray(indices);self.lengths=base.lengths[self.indices]
        assert len(set(self.indices))==len(self.indices)
    def batch(self,indices,starts):
        return self.base.batch(self.indices[np.asarray(indices)],starts)

class FCSeries:
    def __init__(self,base,fc):
        self.base=base;self.fc=torch.from_numpy(fc.astype(np.float32));self.lengths=base.lengths
        assert self.fc.shape==(len(self.lengths),32)
    def batch(self,indices,starts):
        temporal=self.base.batch(indices,starts)
        static=self.fc[np.asarray(indices)].unsqueeze(-1).expand(-1,-1,temporal.shape[-1])
        return torch.cat([temporal,static],dim=1)

class DualNet(nn.Module):
    def __init__(self):
        super().__init__()
        backbone=TemporalNet('tcn')
        self.stem=backbone.stem;self.blocks=backbone.blocks
        self.fc=nn.Sequential(nn.Linear(32,16),nn.GELU(),nn.Dropout(.3))
        self.head=nn.Sequential(nn.Dropout(.3),nn.Linear(80,32),nn.GELU(),nn.Linear(32,1))
    def forward(self,x):
        h=self.blocks(self.stem(x[:,:424]))
        f=self.fc(x[:,424:,0])
        return self.head(torch.cat([h.mean(-1),h.std(-1,unbiased=False),f],1)).flatten()

def select_alpha(y,neural,rbf):
    scores=[float(roc_auc_score(y,a*neural+(1-a)*rbf)) for a in ALPHAS]
    best=next(i for i,s in enumerate(scores) if s>=max(scores)-1e-12)
    return ALPHAS[best],scores

def threshold_on_validation(y,p):
    fpr,tpr,thresholds=roc_curve(y,p)
    valid=np.flatnonzero(np.isfinite(thresholds))
    return float(thresholds[valid[np.argmax((tpr-fpr)[valid])]])

def load_data():
    assert json.loads((REFERENCE/'verification.json').read_text())['status']=='verified'
    cohort=pd.read_csv(REFERENCE/'cohort.csv');splits=pd.read_csv(REFERENCE/'splits.csv')
    assert cohort.subject_id.nunique()==len(cohort)==378
    assert not cohort[['label_conflict','age_conflict','sex_conflict']].any().any()
    y=cohort.label.to_numpy(np.int64)
    for col in ['structural_label','fmri_label','roi_label','participant_label']:
        np.testing.assert_array_equal(y,cohort[col])
    vm=json.loads((CACHE/'verification.json').read_text())
    assert vm['effective_sample_interval_seconds']==1.0 and digest(CACHE/'timeseries.npz')==vm['cache_sha256']
    with np.load(CACHE/'timeseries.npz',allow_pickle=False) as z:
        lookup={str(s):i for i,s in enumerate(z['subject_id'])}
        assert len(lookup)==len(z['subject_id'])
        ix=np.array([lookup[s] for s in cohort.subject_id])
        base=Series(z['data'],z['offsets'])
        np.testing.assert_array_equal(base.lengths,z['lengths'])
    old=pd.read_csv(CACHE/'cohort.csv').set_index('subject_id').loc[cohort.subject_id]
    np.testing.assert_array_equal(old.label,y)
    series=MappedSeries(base,ix)
    fv=json.loads((FEATURES/'verification.json').read_text())
    assert digest(FEATURES/'features.npz')==fv['cache_sha256']
    with np.load(FEATURES/'features.npz',allow_pickle=False) as z:
        lookup={str(s):i for i,s in enumerate(z['subject_id'])}
        assert len(lookup)==len(z['subject_id'])
        ix=np.array([lookup[s] for s in cohort.subject_id])
        np.testing.assert_array_equal(z['label'][ix],y)
        fc=z['fc_summary'][ix];edges=z['fc_edges'][ix]
    assert np.isfinite(fc).all() and np.isfinite(edges).all()
    partitions=make_splits(cohort)
    for fold,tr,va,te in partitions:
        for role,idx in [('train',tr),('validation',va),('test',te)]:
            frame=splits[splits.fold.eq(fold)&splits.role.eq(role)]
            assert frame.subject_id.tolist()==cohort.subject_id.iloc[idx].tolist()
            np.testing.assert_array_equal(frame.label,y[idx])
    return cohort,splits,series,fc,edges,partitions

def summarize(out):
    p=pd.read_csv(out/'predictions.csv');rows=[];bins=[]
    assert len(p)==378*len(MODELS) and not p.duplicated(['model','subject_id']).any()
    for (fold,model),g in p.groupby(['fold','model']):
        y=g.y.to_numpy();s=g.probability.to_numpy();r=dict(fold=int(fold),model=model,auc=float(roc_auc_score(y,s)),ap=float(average_precision_score(y,s)),brier=float(brier_score_loss(y,s)))
        for name,t in [('default',.5),('validation',g.threshold.iloc[0])]:
            tn,fp,fn,tp=confusion_matrix(y,s>=t,labels=[0,1]).ravel()
            r.update({name+'_'+k:int(v) for k,v in zip(['tn','fp','fn','tp'],[tn,fp,fn,tp])})
            r[name+'_balanced_accuracy']=float(.5*(tp/(tp+fn)+tn/(tn+fp)))
        rows.append(r)
        for b in range(5):
            mask=(s>=b/5)&((s<(b+1)/5) if b<4 else (s<=1))
            if mask.any(): bins.append(dict(fold=int(fold),model=model,bin=b,n=int(mask.sum()),mean_score=float(s[mask].mean()),observed_fraction=float(y[mask].mean())))
    result=pd.DataFrame(rows);result.to_csv(out/'fold_metrics.csv',index=False)
    summary=result.groupby('model').agg(mean_auc=('auc','mean'),sd_auc=('auc','std'),mean_ap=('ap','mean'),mean_brier=('brier','mean'),mean_validation_threshold_ba=('validation_balanced_accuracy','mean')).reset_index()
    summary.to_csv(out/'summary.csv',index=False);pd.DataFrame(bins).to_csv(out/'calibration_bins.csv',index=False)
    wide=p.pivot(index=['fold','subject_id','y'],columns='model',values='probability').reset_index()
    groups=[g.reset_index(drop=True) for _,g in wide.groupby('fold')];rng=np.random.default_rng(2026)
    resamples=[[np.concatenate([rng.choice(np.flatnonzero(g.y.to_numpy()==c),(g.y==c).sum(),replace=True) for c in [0,1]]) for g in groups] for _ in range(1000)]
    comparisons=[]
    for a,b in [('late_tcn_rbf','fc_rbf'),('tcn_fc','tcn'),('late_dual_rbf','fc_rbf'),('tcn','fc_rbf'),('late_tcn_rbf','tcn')]:
        point=np.mean([rank_auc(g.y.to_numpy(),g[a].to_numpy())-rank_auc(g.y.to_numpy(),g[b].to_numpy()) for g in groups])
        draws=[np.mean([rank_auc(g.y.to_numpy()[ix],g[a].to_numpy()[ix])-rank_auc(g.y.to_numpy()[ix],g[b].to_numpy()[ix]) for g,ix in zip(groups,rr)]) for rr in resamples]
        comparisons.append(dict(candidate=a,reference=b,delta_mean_auc=float(point),ci_low=float(np.quantile(draws,.025)),ci_high=float(np.quantile(draws,.975)),primary=a=='late_tcn_rbf' and b=='fc_rbf',posthoc_context=a=='late_tcn_rbf' and b=='tcn',caveat='Conditional fixed OOF bootstrap, fold/label stratified; no retraining or split uncertainty, no multiplicity adjustment.'))
    pd.DataFrame(comparisons).to_csv(out/'paired_bootstrap.csv',index=False)
    return summary

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--smoke',action='store_true');args=parser.parse_args()
    torch.set_num_threads(4)
    out=BASE/'runs'/datetime.now().strftime('tcn_fc_completion_%Y%m%d_%H%M%S');out.mkdir()
    protocol=dict(status='preflight',smoke_only=args.smoke,models=MODELS,n=378,device='cpu',threads=4,
        reference=str(REFERENCE),cache=str(CACHE),primary='late_tcn_rbf minus fc_rbf; mean outer-fold AUC',
        data='Audited378;13 label conflicts excluded; exact existing201/51/126 train/val/test partitions.',
        neural='128 contiguous samples at1Hz,5 fixed inference crops;60epochs max,patience12,lr.0003,AdamW weight_decay.01,batch16;seed1200+fold;single seed per fold.',
        fc_rbf='848 FC summaries only;fixed C=.3,gamma=scale,balanced;3fold train-only sigmoid calibration. Scaling inside each calibration training fold.',
        dual='TCN 64 pooled features +16-dimensional MLP encoding of32 train-fitted FC PCA components; joint neural head.',
        alpha_grid=ALPHAS,alpha_selection='Inner validation AUC only; ties favor smaller neural weight. Both branch checkpoints also selected on same validation, so selection optimism remains.',
        threshold='Max Youden J on inner validation only; no test-fitted threshold.',
        missing='No new BrainLM finetuning, permutation importance, permutation significance or external validation.',
        deviation_from_slides='Clean378/3fold and contiguous128-point windows replace historical409/4fold warped192 points. No age/sex/site/QC or structural imaging features.',
        interpretation='Adaptive internal development, not untouched test or clinical diagnostic validation.0.622 is historical, not a directly paired target.')
    save_json(out/'protocol.json',protocol)
    for filename in ['run_tcn_fc_completion.py','run_temporal.py','temporal_models.py']:
        (out/filename).write_bytes((BASE/filename).read_bytes())
    started=time.monotonic();cohort,splits,series,fc,edges,folds=load_data();y=cohort.label.to_numpy(np.int64)
    cohort.to_csv(out/'cohort.csv',index=False);splits.to_csv(out/'splits.csv',index=False)
    protocol.update(status='running',cohort_sha256=digest(REFERENCE/'cohort.csv'),split_sha256=digest(REFERENCE/'splits.csv'),feature_sha256=digest(FEATURES/'features.npz'),temporal_sha256=digest(CACHE/'timeseries.npz'),torch=torch.__version__)
    save_json(out/'protocol.json',protocol);preds=[];vals=[];selection=[];training=[];windows=[]
    with threadpool_limits(limits=4):
        for fold,tr,va,te in folds:
            print('START FOLD',fold,'train',len(tr),'validation',len(va),'test',len(te),flush=True)
            prep=joblib.load(REFERENCE/f'fold{fold}_transforms.joblib')
            assert set(prep['fitted_subject_ids'])==set(cohort.subject_id.iloc[tr])
            pc=prep['pc_scaler'].transform(prep['pca'].transform(prep['edge_scaler'].transform(edges))).astype(np.float32)
            dual_series=FCSeries(series,pc)
            if args.smoke:
                for model,ss in [(TemporalNet('tcn'),series),(DualNet(),dual_series)]:
                    t=time.monotonic();xb=ss.batch(tr[:16],np.zeros(16,dtype=int));loss=model(xb).square().mean();loss.backward();assert torch.isfinite(loss)
                    print('SMOKE',type(model).__name__,time.monotonic()-t,flush=True)
                save_json(out/'smoke.json',dict(status='passed',only_training_subjects=True));print('OUTPUT',out,flush=True);return
            svm=CalibratedClassifierCV(make_pipeline(StandardScaler(),SVC(C=.3,gamma='scale',class_weight='balanced')),method='sigmoid',cv=StratifiedKFold(3,shuffle=True,random_state=700+fold),ensemble=True)
            svm.fit(fc[tr],y[tr]);joblib.dump(svm,out/f'fold{fold}_fc_rbf.joblib')
            validation={'fc_rbf':svm.predict_proba(fc[va])[:,1]};testing={'fc_rbf':svm.predict_proba(fc[te])[:,1]}
            for name,ss,factory in [('tcn',series,None),('tcn_fc',dual_series,DualNet)]:
                model,info=fit(name,ss,y,tr,va,fold,'cpu',out,factory=factory)
                validation[name],_,vw=predict_subjects(model,ss,va);testing[name],_,tw=predict_subjects(model,ss,te)
                training.append(dict(fold=fold,model=name,**info))
                for role,ww in [('validation',vw),('test',tw)]:
                    windows.extend(dict(fold=fold,model=name,role=role,subject_id=cohort.subject_id.iloc[r['index']],**r) for r in ww)
                pd.DataFrame(training).to_csv(out/'training_summary.csv',index=False)
            for name,branch in [('late_tcn_rbf','tcn'),('late_dual_rbf','tcn_fc')]:
                alpha,scores=select_alpha(y[va],validation[branch],validation['fc_rbf'])
                selection.extend(dict(fold=fold,model=name,alpha=a,validation_auc=s,selected=a==alpha) for a,s in zip(ALPHAS,scores))
                validation[name]=alpha*validation[branch]+(1-alpha)*validation['fc_rbf']
                testing[name]=alpha*testing[branch]+(1-alpha)*testing['fc_rbf']
            for name in MODELS:
                threshold=threshold_on_validation(y[va],validation[name])
                for role,idx,values,rows in [('validation',va,validation[name],vals),('test',te,testing[name],preds)]:
                    rows.extend(dict(fold=fold,model=name,subject_id=cohort.subject_id.iloc[i],y=int(y[i]),probability=float(p),threshold=threshold) for i,p in zip(idx,values))
            for filename,rows in [('predictions',preds),('validation_predictions',vals),('alpha_selection',selection),('window_predictions',windows)]:
                pd.DataFrame(rows).to_csv(out/(filename+'.csv'),index=False)
            print('FINISHED FOLD',fold,'test metrics withheld until all folds complete',flush=True)
    summary=summarize(out)
    save_json(out/'complete.json',dict(status='complete_pending_independent_replay',seconds=time.monotonic()-started,neural_fits=6,rbf_calibrated_ensembles=3))
    protocol['status']='complete_pending_independent_replay';save_json(out/'protocol.json',protocol)
    print(summary.to_string(index=False),flush=True);print('OUTPUT',out,flush=True)

if __name__=='__main__':main()
