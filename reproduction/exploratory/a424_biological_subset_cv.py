"""New, non-frozen script: compare a biologically-motivated A424 node subset
(fronto-striatal-thalamic circuit mapped via Glasser HCP-MMP lobe/module table,
148 of 424 nodes) against the full 424-node tangent-space functional connectivity,
under the SAME CV splits, SAME cohort, SAME tangent/ANOVA/LR/MLP design as
run_structural_fusion_locked.py's functional arm. CV only (no LOSO). Reuses the
already-frozen, hash-verified covariances.npy (no raw time-series recomputation).
Does not modify any frozen file; writes only to a new run directory.
"""
from pathlib import Path
import sys, json, time
BASE = Path(__file__).resolve().parent  # /home/seedna2/ML/adhd-local
sys.path.insert(0, str(BASE / 'vendor/connectome0121'))
sys.path.insert(0, str(BASE))
import numpy as np
import pandas as pd
import torch
from threadpoolctl import threadpool_limits
from nilearn.connectome import sym_matrix_to_vec
from nilearn.connectome.connectivity_matrices import _geometric_mean
from run_functional_fusion import train_neural, predict, save_json  # noqa: E402
from refine_tangent_reference import transform  # noqa: E402
from run_connectome_representations import select_features  # noqa: E402

torch.set_num_threads(4)  # match the frozen pipeline's proven setting; avoids
                          # BLAS thread oversubscription that made the first
                          # (unlimited-thread) attempt at this script ~20x slower
from structural_biological_subset_cv import fit_lr, fit_mlp, PARENT, QC, COHORT_NAME  # noqa: E402

COV0 = BASE / 'runs/structural_fusion_locked_20260909/covariances.npy'
COV0_META = BASE / 'runs/structural_fusion_locked_20260909/covariances.json'
COHORT378 = PARENT / 'cohort.csv'
BIO_NODES_FILE = BASE / 'a424_biological_subset_node_indices.txt'
OUT = BASE / 'runs/a424_biological_subset_cv_20260918'


def tangent_scores(cov_arm, y, tr, va, te, fold, tag, folder):
    with __import__('warnings').catch_warnings(record=True):
        __import__('warnings').simplefilter('always')
        mean = _geometric_mean(cov_arm[tr], max_iter=100, tol=1e-8)
    white, logs = transform(cov_arm, mean)
    residual = float(np.linalg.norm(logs[tr].mean(axis=0)) / mean.size)
    raw = sym_matrix_to_vec(logs, discard_diagonal=True).astype(np.float32)
    tx, order, tscale = select_features(raw, y, tr, k=1000)
    p_lr = fit_lr(tx, y, tr, va, te)
    p_mlp = fit_mlp(tx, y, tr, va, te, fold, tag, folder)
    return p_lr, p_mlp, residual


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    q = json.loads(QC.read_text())
    c0 = pd.read_csv(COHORT378)
    sp_all = pd.read_csv(PARENT / 'splits.csv')
    subj_ids = q['cohorts'][COHORT_NAME]
    c = c0[c0.subject_id.isin(subj_ids)].copy().reset_index(drop=True)
    sp = sp_all[sp_all.subject_id.isin(c.subject_id)].copy()
    assert len(c) == len(subj_ids)

    meta = json.loads(COV0_META.read_text())
    assert meta['ids'] == c0.subject_id.tolist()
    cov0 = np.load(COV0, mmap_mode='r')
    ci = {s: i for i, s in enumerate(c0.subject_id)}
    cov_full = np.asarray(cov0[[ci[s] for s in c.subject_id]])
    assert cov_full.shape == (len(c), 424, 424)

    bio_idx = np.array([int(x) for x in BIO_NODES_FILE.read_text().split()])
    assert len(bio_idx) == 148 and bio_idx.max() < 424
    cov_bio = cov_full[:, bio_idx][:, :, bio_idx]
    print('bio covariance shape', cov_bio.shape, flush=True)

    y_all = c.label.to_numpy(np.int64)
    lookup = {sid: i for i, sid in enumerate(c.subject_id)}
    rows = []
    t0 = time.time()
    from sklearn.metrics import roc_auc_score
    with threadpool_limits(limits=4):
        for r in range(1, 6):
            for f in range(1, 4):
                fold_dir = OUT / f'repeat{r}_fold{f}'
                fold_dir.mkdir(exist_ok=True, parents=True)
                group = sp[sp.repeat.eq(r) & sp.fold.eq(f)]
                tr, va, te = [np.array([lookup[s] for s in group[group.role.eq(role)].subject_id])
                              for role in ['train', 'validation', 'test']]
                assert not (set(tr) & set(va) or set(tr) & set(te) or set(va) & set(te))
                y = y_all
                for tag, cov_arm in [('full424', cov_full), ('bio148', cov_bio)]:
                    p_lr, p_mlp, residual = tangent_scores(cov_arm, y, tr, va, te, f, f'{tag}_r{r}', fold_dir)
                    for model_name, p in [(f'tangent_lr_{tag}', p_lr), (f'tangent_mlp_{tag}', p_mlp)]:
                        auc = float(roc_auc_score(y[te], p))
                        rows.append(dict(repeat=r, fold=f, model=model_name, n_test=len(te), auc=auc, residual=residual))
                pd.DataFrame(rows).to_csv(OUT / 'fold_metrics_partial.csv', index=False)
                print(f'repeat{r} fold{f} done at {time.time()-t0:.1f}s', flush=True)

    fm = pd.DataFrame(rows)
    fm.to_csv(OUT / 'fold_metrics.csv', index=False)
    rm = fm.groupby(['repeat', 'model'])['auc'].mean().reset_index()
    rm.to_csv(OUT / 'repeat_metrics.csv', index=False)
    summary = rm.groupby('model')['auc'].agg(['mean', 'min', 'max']).reset_index()
    summary.to_csv(OUT / 'summary.csv', index=False)
    print(summary.to_string(index=False), flush=True)
    save_json(OUT / 'status.json', dict(status='complete', cohort=COHORT_NAME, elapsed_seconds=time.time() - t0))


if __name__ == '__main__':
    main()
