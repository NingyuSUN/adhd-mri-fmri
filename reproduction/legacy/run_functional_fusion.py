"""Paired functional/fusion CPU development run. No structural-only training."""
import argparse
import copy
import hashlib
import json
import random
import time
from datetime import datetime
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import torch
from torch import nn
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score, balanced_accuracy_score, brier_score_loss
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.svm import SVC
from threadpoolctl import threadpool_limits
from build_multimodal_manifest import norm_id, digest

BASE = Path(__file__).resolve().parent
AUDIT = BASE / 'runs/multimodal_inventory_20260907_122809'
FEATURES = BASE / 'runs/features_20260907_111310'
MODELS = ['fmri_rbf', 'fusion_rbf', 'fmri_mlp', 'fusion_mlp',
          'confounds_lr', 'confounds_fmri_lr', 'confounds_fusion_lr']


def save_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')


def make_splits(cohort):
    assert cohort.subject_id.is_unique
    strata = cohort.site.astype(str) + '__' + cohort.label.astype(int).astype(str)
    assert strata.value_counts().min() >= 3
    result = []
    for fold, (tv, te) in enumerate(StratifiedKFold(3, shuffle=True, random_state=2026).split(cohort, strata), 1):
        tr, va = train_test_split(tv, test_size=.20, stratify=cohort.label.to_numpy()[tv], random_state=900+fold)
        groups = [set(cohort.subject_id.iloc[idx]) for idx in [tr, va, te]]
        assert not (groups[0] & groups[1] or groups[0] & groups[2] or groups[1] & groups[2])
        assert len(set.union(*groups)) == len(cohort)
        assert set(cohort.site.iloc[tr]) == set(cohort.site)
        for idx in [tr, va, te]:
            assert set(cohort.label.iloc[idx]) == {0, 1}
        result.append((fold, tr, va, te))
    assert sorted(np.concatenate([t[3] for t in result])) == list(range(len(cohort)))
    return result


class MLP(nn.Module):
    def __init__(self, features):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(features, 64), nn.GELU(), nn.Dropout(.4),
                                 nn.Linear(64, 16), nn.GELU(), nn.Dropout(.3), nn.Linear(16, 1))

    def forward(self, x):
        return self.net(x).flatten()


@torch.no_grad()
def predict(model, x, idx):
    model.eval()
    return torch.sigmoid(model(x[idx])).numpy()


def train_neural(x, y, tr, va, fold, name, out, seed=None):
    seed = 1200 + fold if seed is None else seed
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    x = torch.from_numpy(x.astype(np.float32))
    target = torch.from_numpy(y.astype(np.float32))
    model = MLP(x.shape[1])
    opt = torch.optim.AdamW(model.parameters(), lr=.001, weight_decay=.01)
    criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(float((y[tr] == 0).sum() / (y[tr] == 1).sum())))
    rng = np.random.default_rng(seed)
    best, state, best_epoch, wait = -1., None, 0, 0
    history = []
    for epoch in range(1, 81):
        model.train(); loss_sum = 0.
        order = rng.permutation(tr)
        for offset in range(0, len(order), 16):
            batch = order[offset:offset+16]
            opt.zero_grad(); loss = criterion(model(x[batch]), target[batch])
            assert torch.isfinite(loss)
            loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step()
            loss_sum += float(loss.detach()) * len(batch)
        p = predict(model, x, va)
        auc = float(roc_auc_score(y[va], p))
        history.append({'epoch': epoch, 'train_loss': loss_sum/len(tr), 'val_auc': auc})
        if auc > best + 1e-4:
            best, state, best_epoch, wait = auc, copy.deepcopy(model.state_dict()), epoch, 0
        else:
            wait += 1
        if wait >= 12:
            break
    model.load_state_dict(state)
    torch.save({'state_dict': state, 'input_features': x.shape[1]}, out / f'fold{fold}_{name}.pt')
    pd.DataFrame(history).to_csv(out / f'fold{fold}_{name}_history.csv', index=False)
    return model, x, {'best_epoch': best_epoch, 'epochs_run': epoch, 'best_val_auc': best,
                      'parameters': sum(t.numel() for t in model.parameters())}


def metrics(y, p):
    return {'auc': float(roc_auc_score(y, p)), 'ap': float(average_precision_score(y, p)),
            'balanced_accuracy': float(balanced_accuracy_score(y, p >= .5)),
            'brier': float(brier_score_loss(y, p))}


def bootstrap(predictions, out, repetitions=1000):
    pairs = [('fusion_mlp', 'fmri_mlp'), ('fusion_rbf', 'fmri_rbf'),
             ('confounds_fmri_lr', 'confounds_lr'), ('confounds_fusion_lr', 'confounds_fmri_lr')]
    table = predictions.pivot(index=['fold', 'subject_id', 'y'], columns='model', values='probability').reset_index()
    assert not table[MODELS].isna().any().any()
    rng = np.random.default_rng(2026)
    rows = []
    for candidate, reference in pairs:
        subsets = [g.reset_index(drop=True) for _, g in table.groupby('fold')]
        point = np.mean([roc_auc_score(g.y, g[candidate])-roc_auc_score(g.y, g[reference]) for g in subsets])
        draws = []
        for _ in range(repetitions):
            changes = []
            for g in subsets:
                yy = g.y.to_numpy()
                ix = np.concatenate([rng.choice(np.flatnonzero(yy == label), (yy == label).sum(), replace=True) for label in [0, 1]])
                changes.append(roc_auc_score(yy[ix], g[candidate].to_numpy()[ix])-roc_auc_score(yy[ix], g[reference].to_numpy()[ix]))
            draws.append(np.mean(changes))
        rows.append({'candidate': candidate, 'reference': reference, 'mean_fold_auc_difference': point,
                     'conditional_ci_low': float(np.quantile(draws, .025)),
                     'conditional_ci_high': float(np.quantile(draws, .975)), 'replicates': repetitions,
                     'caveat': 'Fixed-OOF paired subject bootstrap within fold and label; excludes training/split variability; no multiplicity adjustment.'})
    pd.DataFrame(rows).to_csv(out / 'paired_bootstrap.csv', index=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    torch.set_num_threads(4)
    out = BASE / 'runs' / datetime.now().strftime('functional_fusion_%Y%m%d_%H%M%S')
    out.mkdir()
    cohort = pd.read_csv(AUDIT / 'paired_clean_metadata409.csv').sort_values(['site', 'subject_id']).reset_index(drop=True)
    assert len(cohort) == 378 and cohort.subject_id.nunique() == 378
    assert not cohort[['label_conflict', 'age_conflict', 'sex_conflict']].any().any()
    for col in ['structural_label', 'fmri_label', 'roi_label', 'participant_label']:
        assert np.array_equal(cohort.label, cohort[col]), col
    assert cohort.anatomical_metadata_qc_pass.all()
    assert cohort.has_roi_metadata.all()
    assert set(cohort.motion_status).issubset({'ok', 'HTTPError'})
    y = cohort.label.to_numpy(dtype=np.int64)
    roi = pd.read_csv(AUDIT / 'structural_roi_features_with_provenance.csv').set_index('subject_id')
    assert roi.index.is_unique
    roi = roi.loc[cohort.subject_id]
    assert np.array_equal(roi.binary_label, y)
    assert np.array_equal(roi.site, cohort.site)
    roi_columns = [c for c in roi if c.startswith('cort_') or c.startswith('sub_')]
    assert len(roi_columns) == 20
    s = roi[roi_columns].to_numpy(dtype=np.float32)
    assert np.isfinite(s).all()
    folds = make_splits(cohort)
    rows = []
    for fold, tr, va, te in folds:
        for role, idx in [('train', tr), ('validation', va), ('test', te)]:
            rows.extend({'fold': fold, 'role': role, 'subject_id': cohort.subject_id.iloc[i],
                         'site': cohort.site.iloc[i], 'label': int(y[i])} for i in idx)
    cohort.to_csv(out / 'cohort.csv', index=False)
    pd.DataFrame(rows).to_csv(out / 'splits.csv', index=False)
    protocol = {'status': 'prepared', 'models': MODELS, 'n_subjects': len(cohort),
        'no_structural_only_model': True, 'neuroimage_permission': 'User explicitly confirmed project training permission in this conversation before run.',
        'cohort_rule': 'Existing historical409 paired assets, no label/age/sex conflict, structural metadata QC pass. All13 unresolved labels quarantined. No performance-based exclusions.',
        'interpretation': 'Exploratory internal development on reused data; no independent holdout or clinical validation.',
        'structural_input': '20 atlas ROI mean subject-normalized T1 intensities, not morphometry; code-supported paired metadata export, not newly reconstructed from raw MRI.',
        'fmri_rbf_input': '848 FC summaries +848 spectra +256 existing frozen BrainLM embeddings',
        'fmri_mlp_input': '32 train-fitted PCA components of 89676 FC edges',
        'fusion_input': 'Corresponding functional input concatenated with20 existing structural ROI intensities',
        'outer': '3-fold stratified site x label; seed2026; subject level',
        'inner': '20% of outer-training, label-stratified; seed900+fold; same inner train used by all7 models',
        'mlp': {'hidden': [64,16], 'activation': 'GELU', 'dropout': [.4,.3], 'epochs_max':80,'patience':12,'lr':.001,'weight_decay':.01,'batch_size':16,'seed':'1200+fold'},
        'svm': {'C':.3, 'gamma':'scale','class_weight':'balanced','probability':True,'random_state':42},
        'logistic': {'C':.03,'class_weight':'balanced','solver':'liblinear'},
        'preprocessing': 'All imputation, scaling, PCA and one-hot encoder fit on each inner training subset only.',
        'test_policy': 'No test-based model, hyperparameter, epoch, cohort or split selection. Report every fixed model.',
        'primary_contrast': 'fusion_mlp minus fmri_mlp, mean fold AUC; additional ML and confound increments secondary',
        'prepare_only': args.prepare_only, 'device':'CPU', 'threads':4,
        'motion_missing_policy': 'Keep3 people with failed historical motion retrieval; train-only median imputation plus explicit availability flag in covariate models. Imaging inputs are present.',
        'motion_status_counts': {str(k):int(v) for k,v in cohort.motion_status.value_counts().items()},
        'sources': {str(p): digest(p) for p in [AUDIT/'subject_modality_manifest.csv', AUDIT/'structural_roi_features_with_provenance.csv', FEATURES/'verification.json']}}
    save_json(out/'protocol.json', protocol)
    (out/'experiment_source.py').write_text(Path(__file__).read_text(encoding='utf-8'), encoding='utf-8')
    if args.prepare_only:
        print('PREPARED',out,flush=True); return
    verify = json.loads((FEATURES/'verification.json').read_text())
    assert verify['one_hz_unverified'] == verify['one_hz_mismatches'] == 0
    print('Verifying feature cache...',flush=True)
    assert digest(FEATURES/'features.npz') == verify['cache_sha256']
    with np.load(FEATURES/'features.npz', allow_pickle=False) as z:
        ids = [norm_id(x) for x in z['subject_id']]
        assert len(ids) == len(set(ids))
        positions = {sid:i for i,sid in enumerate(ids)}
        idx = np.array([positions[sid] for sid in cohort.subject_id])
        assert np.array_equal(z['label'][idx], y)
        assert np.array_equal(z['site'][idx], cohort.site)
        edges = z['fc_edges'][idx]
        historical = np.c_[z['fc_summary'][idx],z['spectral'][idx],z['brainlm'][idx]]
    assert np.isfinite(edges).all() and np.isfinite(historical).all()
    protocol['feature_sha256'] = verify['cache_sha256']
    protocol['status'] = 'running'; save_json(out/'protocol.json', protocol)
    confound_cols = ['structural_age','structural_sex_male','mean_fd','max_fd','pct_fd_gt_0p2','mean_dvars','n_volumes']
    confounds = np.c_[cohort[confound_cols].to_numpy(dtype=float),cohort.rest_metadata_qc_pass.to_numpy(dtype=float),cohort.motion_status.eq('ok').to_numpy(dtype=float)]
    all_metrics, all_predictions, validation_predictions = [], [], []
    start = time.perf_counter()
    with threadpool_limits(limits=4):
        for fold,tr,va,te in folds:
            print(f'FOLD {fold}: train={len(tr)} validation={len(va)} test={len(te)}',flush=True)
            edge_scaler = StandardScaler().fit(edges[tr])
            scaled = edge_scaler.transform(edges)
            pca = PCA(n_components=32,svd_solver='randomized',random_state=2026).fit(scaled[tr])
            pc0 = pca.transform(scaled)
            pc_scaler = StandardScaler().fit(pc0[tr]); pc = pc_scaler.transform(pc0).astype(np.float32)
            structural_scaler = StandardScaler().fit(s[tr]); structural = structural_scaler.transform(s).astype(np.float32)
            encoder = OneHotEncoder(handle_unknown='ignore',sparse_output=False).fit(cohort[['site']].iloc[tr])
            cov = np.c_[encoder.transform(cohort[['site']]),confounds]
            inputs = {'fmri_rbf':historical,'fusion_rbf':np.c_[historical,s],
                      'fmri_mlp':pc,'fusion_mlp':np.c_[pc,structural],
                      'confounds_lr':cov,'confounds_fmri_lr':np.c_[cov,pc],
                      'confounds_fusion_lr':np.c_[cov,pc,structural]}
            joblib.dump({'edge_scaler':edge_scaler,'pca':pca,'pc_scaler':pc_scaler,'structural_scaler':structural_scaler,
                         'site_encoder':encoder,'fitted_subject_ids':cohort.subject_id.iloc[tr].tolist(),
                         'roi_columns':roi_columns,'confound_columns':confound_cols+['rest_metadata_qc_pass','motion_available']},out/f'fold{fold}_transforms.joblib')
            for name in MODELS:
                begun = time.perf_counter(); info = {}
                x = inputs[name]
                if name.endswith('_mlp'):
                    model,xt,info = train_neural(x,y,tr,va,fold,name,out)
                    p = predict(model,xt,te); vp = predict(model,xt,va)
                    assert abs(roc_auc_score(y[va],vp)-info['best_val_auc']) < 1e-12
                else:
                    estimator = SVC(C=.3,gamma='scale',class_weight='balanced',probability=True,random_state=42) if name.endswith('_rbf') else LogisticRegression(C=.03,class_weight='balanced',max_iter=4000,solver='liblinear',random_state=42)
                    pipeline = make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),estimator)
                    pipeline.fit(x[tr],y[tr]); p = pipeline.predict_proba(x[te])[:,1]; vp = pipeline.predict_proba(x[va])[:,1]
                    joblib.dump(pipeline,out/f'fold{fold}_{name}.joblib')
                assert np.isfinite(p).all() and ((p>=0)&(p<=1)).all()
                record = {'fold':fold,'model':name,'n_train':len(tr),'n_validation':len(va),'n_test':len(te),
                          **metrics(y[te],p),**info,'seconds':time.perf_counter()-begun}
                all_metrics.append(record)
                for target,indices,probs in [(all_predictions,te,p),(validation_predictions,va,vp)]:
                    target.extend({'fold':fold,'model':name,'subject_id':cohort.subject_id.iloc[i],
                                   'site':cohort.site.iloc[i],'y':int(y[i]),'probability':float(prob)} for i,prob in zip(indices,probs))
                pd.DataFrame(all_metrics).to_csv(out/'fold_metrics.csv',index=False)
                pd.DataFrame(all_predictions).to_csv(out/'predictions.csv',index=False)
                pd.DataFrame(validation_predictions).to_csv(out/'validation_predictions.csv',index=False)
                print(f"TEST fold={fold} {name}: AUC={record['auc']:.4f}",flush=True)
    pred = pd.DataFrame(all_predictions); metric_df = pd.DataFrame(all_metrics)
    summary = metric_df.groupby('model').agg(mean_auc=('auc','mean'),sd_auc=('auc','std'),mean_ap=('ap','mean'),mean_balanced_accuracy=('balanced_accuracy','mean'),mean_brier=('brier','mean')).reset_index()
    for i,r in summary.iterrows():
        sub = pred[pred.model == r.model].set_index('subject_id').loc[cohort.subject_id]
        assert sub.index.is_unique and len(sub) == len(cohort)
        summary.loc[i,'pooled_oof_auc'] = roc_auc_score(sub.y,sub.probability)
    summary.to_csv(out/'summary.csv',index=False)
    print('Training complete; paired uncertainty analysis...',flush=True)
    bootstrap(pred,out)
    save_json(out/'complete.json',{'status':'complete','subjects':len(cohort),'model_folds':len(metric_df),
                                  'models':MODELS,'elapsed_seconds':time.perf_counter()-start,'no_structural_only_training':True})
    protocol['status'] = 'complete_pending_replay_verification'; save_json(out/'protocol.json', protocol)
    print(summary.to_string(index=False),flush=True); print('OUTPUT',out,flush=True)


if __name__ == '__main__':
    main()
