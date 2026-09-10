"""Training-only numerical sensitivity audit; no test-label model selection."""
from pathlib import Path
import sys
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE/'vendor/connectome0121'))
import json,time,warnings
from datetime import datetime
import numpy as np
import joblib
from scipy.linalg import eigh
from sklearn.covariance import LedoitWolf
from nilearn.connectome.connectivity_matrices import _geometric_mean
from nilearn.connectome import sym_matrix_to_vec
from threadpoolctl import threadpool_limits
from run_tcn_fc_completion import load_data
from run_functional_fusion import save_json

def transform(covariances,mean):
    val,vec=eigh(mean);assert val.min()>0
    white=(vec/np.sqrt(val))@vec.T
    logs=[]
    for c in covariances:
        a=white@c@white;v,q=eigh((a+a.T)/2);assert v.min()>0
        logs.append((q*np.log(v))@q.T)
    return white,np.asarray(logs)

def main():
    old=BASE/'runs/connectome_representations_20260907_160140'
    assert json.loads((old/'verification.json').read_text())['status']=='verified'
    out=BASE/'runs'/datetime.now().strftime('tangent_refinement_%Y%m%d_%H%M%S');out.mkdir()
    save_json(out/'protocol.json',dict(status='running',parent=str(old),scope='numerical reference refinement only; no new training',max_iter=100,solver_tol=1e-8,actual_residual_acceptance=1e-7,initialization='saved training-only reference',no_test_label_selection=True))
    (out/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    print('OUTPUT',out,flush=True)
    cohort,splits,series,fc,edges,folds=load_data();del fc,edges
    cohort.to_csv(out/'cohort.csv',index=False);splits.to_csv(out/'splits.csv',index=False)
    records=[]
    with threadpool_limits(limits=4):
        cov=[]
        for i in series.indices:
            d=np.asarray(series.base.data[series.base.offsets[i]:series.base.offsets[i+1]],dtype=np.float64)
            cov.append(LedoitWolf(store_precision=False).fit(d).covariance_)
        del series
        for fold,tr,va,te in folds:
            start=time.monotonic();previous=joblib.load(old/f'fold{fold}_tangent.joblib')
            assert previous['fit_ids']==cohort.subject_id.iloc[tr].tolist()
            print('REFINING training-only fold',fold,flush=True)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                mean=_geometric_mean([cov[i] for i in tr],init=previous['measure'].mean_.copy(),max_iter=100,tol=1e-8)
            white,logs=transform(cov,mean)
            residual=float(np.linalg.norm(logs[tr].mean(axis=0))/mean.size)
            tx=sym_matrix_to_vec(logs,discard_diagonal=True).astype(np.float32);del logs
            baseline=np.load(old/f'fold{fold}_tangent.npy')
            difference=tx.astype(np.float64)-baseline
            measure=previous['measure'];measure.mean_=mean;measure.whitening_=white
            joblib.dump(dict(measure=measure,fit_ids=previous['fit_ids']),out/f'fold{fold}_tangent.joblib')
            np.save(out/f'fold{fold}_tangent.npy',tx)
            records.append(dict(fold=fold,residual=residual,passes_original_tolerance=residual<1e-7,passes_solver_tolerance=residual<1e-8,warnings=[str(w.message) for w in caught],feature_rms_change=float(np.sqrt(np.mean(difference**2))),feature_max_change=float(np.abs(difference).max()),seconds=time.monotonic()-start))
            save_json(out/'numerical_audit.json',records);print(records[-1],flush=True)
    save_json(out/'complete.json',dict(status='numerical_audit_complete',all_original_tolerance_passed=all(r['passes_original_tolerance'] for r in records),models_retrained=False))
    print('COMPLETE',out,flush=True)

if __name__=='__main__':main()
