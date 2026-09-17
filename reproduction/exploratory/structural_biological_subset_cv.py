"""New, non-frozen script: compare a biologically-motivated SynthSeg region subset
(fronto-striatal-thalamic circuit: PFC + cingulate + thalamus/caudate/putamen/pallidum/accumbens,
36 of 98 columns) against the full 98-region automatic structural feature set, under the
SAME CV splits, SAME cohort, SAME LR/MLP training design as run_structural_fusion_locked.py.
CV only (no LOSO). Does not modify, import-execute, or overwrite any frozen run directory.
"""
from pathlib import Path
import sys, json, time
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

BASE = Path(__file__).resolve().parent  # expected: /home/seedna2/ML/adhd-local
sys.path.insert(0, str(BASE))
from run_functional_fusion import train_neural, predict, MLP, save_json  # noqa: E402

PARENT = BASE / 'runs/demographic_increment_20260908_locked_v2'
QC = BASE / 'runs/structural_qc_locked_20260909/qc_lock.json'
VOL = BASE / 'runs/structural_features378_20260909/volumes_NOT_TRAINING_READY.npz'
OUT = BASE / 'runs/structural_biological_subset_cv_20260918'
CS = [.01, .1, 1., 10.]
COHORT_NAME = 'primary'

# Biological subset: PFC + cingulate + thalamus/caudate/putamen/pallidum/accumbens (both hemispheres).
# Explicitly excludes amygdala/hippocampus, matching the original notebook's
# USE_EXTENDED=False "core ADHD circuit" choice (not the "extended/limbic" option).
BIO_CORTICAL = ['caudalmiddlefrontal', 'lateralorbitofrontal', 'medialorbitofrontal',
                 'parsopercularis', 'parsorbitalis', 'parstriangularis',
                 'rostralmiddlefrontal', 'superiorfrontal', 'frontalpole',
                 'caudalanteriorcingulate', 'isthmuscingulate', 'posteriorcingulate',
                 'rostralanteriorcingulate']
BIO_SUBCORTICAL = ['thalamus', 'caudate', 'putamen', 'pallidum', 'accumbens area']


def bio_columns(columns):
    idx = []
    names = []
    for i, c in enumerate(columns):
        cl = c.lower()
        if cl.startswith('ctx-lh-') or cl.startswith('ctx-rh-'):
            region = cl.split('-', 2)[2]
            if region in BIO_CORTICAL:
                idx.append(i); names.append(c)
        else:
            base = cl.replace('left ', '').replace('right ', '')
            if base in BIO_SUBCORTICAL:
                idx.append(i); names.append(c)
    return np.array(idx, dtype=int), names


def fit_lr(x, y, tr, va, te):
    models, aucs = [], []
    for cc in CS:
        m = LogisticRegression(C=cc, class_weight='balanced', solver='liblinear',
                                max_iter=5000, random_state=42).fit(x[tr], y[tr])
        models.append(m)
        aucs.append(float(roc_auc_score(y[va], m.predict_proba(x[va])[:, 1])))
    best = next(i for i, v in enumerate(aucs) if v >= max(aucs) - 1e-12)
    return models[best].predict_proba(x[te])[:, 1]


def fit_mlp(x, y, tr, va, te, fold, tag, folder):
    scores = []
    for seed in [1200 + fold, 2200 + fold, 3200 + fold]:
        model, xt, info = train_neural(x, y, tr, va, fold, f'{tag}_seed{seed}', folder, seed=seed)
        scores.append(predict(model, xt, te))
    return np.mean(scores, axis=0)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    q = json.loads(QC.read_text())
    c_all = pd.read_csv(PARENT / 'cohort.csv')
    sp_all = pd.read_csv(PARENT / 'splits.csv')
    subj_ids = q['cohorts'][COHORT_NAME]
    c = c_all[c_all.subject_id.isin(subj_ids)].copy().reset_index(drop=True)
    sp = sp_all[sp_all.subject_id.isin(c.subject_id)].copy()
    assert len(c) == len(subj_ids)

    z = np.load(VOL, allow_pickle=False)
    vi = {s: i for i, s in enumerate(z['subject_id'].astype(str))}
    ix = [vi[s] for s in c.subject_id]
    vol_full = z['volume_fractions'][ix]
    columns = z['columns']
    assert vol_full.shape == (len(c), 98)

    bio_idx, bio_names = bio_columns(columns)
    vol_bio = vol_full[:, bio_idx]
    print('BIO SUBSET', len(bio_idx), 'columns:', list(bio_names), flush=True)
    save_json(OUT / 'bio_subset_columns.json', dict(count=len(bio_idx), columns=list(bio_names)))

    y_all = c.label.to_numpy(np.int64)
    lookup = {sid: i for i, sid in enumerate(c.subject_id)}
    rows = []
    t0 = time.time()
    for r in range(1, 6):
        for f in range(1, 4):
            fold_dir = OUT / f'repeat{r}_fold{f}'
            fold_dir.mkdir(exist_ok=True)
            group = sp[sp.repeat.eq(r) & sp.fold.eq(f)]
            tr, va, te = [np.array([lookup[s] for s in group[group.role.eq(role)].subject_id])
                          for role in ['train', 'validation', 'test']]
            assert not (set(tr) & set(va) or set(tr) & set(te) or set(va) & set(te))
            assert sorted(np.r_[tr, va, te]) == list(range(len(c)))
            y = y_all

            for tag, vol in [('full98', vol_full), ('bio36', vol_bio)]:
                sc = StandardScaler().fit(vol[tr])
                sx = sc.transform(vol).astype(np.float32)
                p_lr = fit_lr(sx, y, tr, va, te)
                p_mlp = fit_mlp(sx, y, tr, va, te, f, f'{tag}_r{r}', fold_dir)
                for model_name, p in [(f'structural_lr_{tag}', p_lr), (f'structural_mlp_{tag}', p_mlp)]:
                    auc = float(roc_auc_score(y[te], p))
                    rows.append(dict(repeat=r, fold=f, model=model_name, n_test=len(te), auc=auc))
            print(f'repeat{r} fold{f} done at {time.time()-t0:.1f}s', flush=True)

    fm = pd.DataFrame(rows)
    fm.to_csv(OUT / 'fold_metrics.csv', index=False)
    rm = fm.groupby(['repeat', 'model'])['auc'].mean().reset_index()
    rm.to_csv(OUT / 'repeat_metrics.csv', index=False)
    summary = rm.groupby('model')['auc'].agg(['mean', 'min', 'max']).reset_index()
    summary.to_csv(OUT / 'summary.csv', index=False)
    print(summary.to_string(index=False), flush=True)
    save_json(OUT / 'status.json', dict(status='complete', cohort=COHORT_NAME,
              elapsed_seconds=time.time() - t0))


if __name__ == '__main__':
    main()
