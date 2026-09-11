"""Analysis v2 confirmatory round. Pre-registration: docs/analysis_v2_protocol.md.

Same 17 model/fusion outputs, same frozen QC lock / features / covariances / splits
as structural_fusion_locked_20260909. Three changes vs that round:
  C1  MLP ensemble seed = base + fold*10 + repeat   (repeat-independent trajectories)
  C2  pre-registered PRIMARY contrast is symmetric: full_fusion_structural_mlp - full_functional_mlp
  C3  two evaluation frameworks:  --framework cv  (re-run of 20260909)
                                  --framework loso (strict leave-one-site-out, new)
Statistics (Nadeau-Bengio corrected CV interval, site-stratified subject bootstrap,
TOST, decision tree) are in analyze_v2_stats.py. This script only produces the
per-fold / per-site model outputs and point metrics, with the same replay checks.
"""
from pathlib import Path
import sys, json, time, warnings, argparse, traceback
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / 'vendor/connectome0121'))
import numpy as np
import pandas as pd
import joblib, torch
from sklearn.covariance import LedoitWolf
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, average_precision_score, balanced_accuracy_score, brier_score_loss
from nilearn.connectome import sym_matrix_to_vec
from nilearn.connectome.connectivity_matrices import _geometric_mean
from threadpoolctl import threadpool_limits
from run_functional_fusion import save_json, digest, train_neural, predict, MLP
from run_structural_fusion_locked import fit_lr, blend, MODEL_NAMES, CS
from run_repeated_connectome import controls
from run_demographic_increment import demographic
from run_connectome_representations import select_features
from refine_tangent_reference import transform
from run_incremental_imaging import choose_alpha, conditional_auc

OUT = BASE / 'runs/structural_fusion_v2_20260910'
PARENT = BASE / 'runs/demographic_increment_20260908_locked_v2'
QC = BASE / 'runs/structural_qc_locked_20260909/qc_lock.json'
VOL = BASE / 'runs/structural_features378_20260909/volumes_NOT_TRAINING_READY.npz'
CACHE = BASE / 'runs/temporal_cache_20260907_113751'
LOCKED = BASE / 'runs/structural_fusion_locked_20260909'
QC_SHA = 'e03ad88399837fb5e894c7eae633acc806082a8cd9dfbd9c1a1180c85608ddc4'
COHORTS = ['primary', 'warning_free', 'include_holds']
SEED_BASES = [1200, 2200, 3200]
SITES = ['KKI', 'NYU', 'NeuroIMAGE', 'OHSU', 'Peking_1', 'Peking_2', 'Peking_3']
DEPENDENCIES = ['run_functional_fusion.py', 'run_structural_fusion_locked.py', 'run_repeated_connectome.py',
                'run_demographic_increment.py', 'run_connectome_representations.py', 'refine_tangent_reference.py',
                'run_incremental_imaging.py', 'vendor/connectome0121/nilearn/connectome/connectivity_matrices.py']
# candidate, reference. P = primary (symmetric MLP). S* / E1 = secondary / descriptive.
CONTRASTS = [
    ('full_fusion_structural_mlp', 'full_functional_mlp'),   # P  PRIMARY
    ('full_functional_mlp', 'full_covariates_lr'),           # S1
    ('full_fusion_mlp', 'full_functional_mlp'),              # S2
    ('full_fusion_lr', 'full_functional_lr'),                # S3
    ('image_fusion_mlp', 'tangent_mlp'),                     # S4
    ('full_fusion_tiv_mlp', 'full_functional_tiv_mlp'),      # S5
    ('structural_mlp', 'structural_lr'),                     # E1
]
PRIMARY_CONTRAST = list(CONTRASTS[0])
EQUIV_MARGIN = 0.02


def protocol():
    return dict(
        analysis='structural_fusion_v2', preregistration='docs/analysis_v2_protocol.md',
        parent_round='structural_fusion_locked_20260909', qc_sha256=QC_SHA, cohorts=COHORTS,
        C=CS, alpha=[0, .25, .5, .75, 1], models=MODEL_NAMES,
        primary_contrast=PRIMARY_CONTRAST, comparisons=[list(x) for x in CONTRASTS],
        equivalence_margin=EQUIV_MARGIN,
        changes_vs_parent=dict(
            C1_seed='base + fold*10 + repeat (cv);  base + site_index (loso)',
            C2_primary_contrast='full_fusion_structural_mlp minus full_functional_mlp (symmetric MLP)',
            C3_frameworks='cv (saved 5x3 splits, re-run) and loso (7 held-out sites, single stratified inner holdout for C/alpha/early-stop)'),
        loso=dict(sites=SITES, inner='stratified 85/15 holdout of the training sites, stratified by site x label, random_state=2026+site_index',
                  primary_metric='within-site pair-weighted AUC over the 7 held-out sites (conditional_auc)',
                  secondary_metrics=['unweighted macro AUC', 'pooled OOF AUC'],
                  sensitivity='drop sites with n<20 (Peking_2, Peking_3)'),
        structural='98 region/TIV fractions, not cortical thickness',
        functional='tangent geometric mean + LedoitWolf + ANOVA top1000 + scaler, all train-only',
        lr='balanced L2 liblinear max_iter5000 seed42; validation AUC selects C, ties smaller C',
        mlp=dict(hidden=[64, 16], activation='GELU', dropout=[.4, .3], epochs_max=80, patience=12,
                 lr=.001, weight_decay=.01, batch=16, clip=1., seeds='SEED_BASES + offset; equal 3-seed ensemble'),
        fusion='validation-only convex weights; ties prefer less added modality; sequential covariate+functional then structural',
        metrics='cv: mean fold AUC then mean over 5 repeats; loso: pair-weighted AUC over 7 sites. within-site pair-weighted AUC secondary. AP/BA0.5/Brier descriptive. repeat/site range is NOT a CI.',
        caveat='Adaptive reused internal cohort; validation carries multi-stage selection; no external validation or clinical-risk calibration; sampled assistant QC.',
        input_hashes={str(p.relative_to(BASE)).replace('\\', '/'): digest(p)
                      for p in [QC, VOL, PARENT / 'cohort.csv', PARENT / 'splits.csv', CACHE / 'verification.json']},
        code_hashes={Path(name).as_posix(): digest(BASE / name) for name in [Path(__file__).name] + DEPENDENCIES})


def prepare():
    assert digest(QC) == QC_SHA
    q = json.loads(QC.read_text())
    assert q['reviewed'] == 378 and q['dense_reviewed'] == 76
    assert digest(VOL) == q['feature_sha256']
    c = pd.read_csv(PARENT / 'cohort.csv')
    sp = pd.read_csv(PARENT / 'splits.csv')
    assert c.subject_id.is_unique and len(c) == 378 and not c[['label_conflict', 'age_conflict', 'sex_conflict']].any().any()
    assert set(c.subject_id) == {r['subject_id'] for r in q['subjects']}
    assert not sp.duplicated(['repeat', 'fold', 'subject_id']).any()
    spec = protocol()
    if (OUT / 'protocol_v2.json').exists():
        assert json.loads((OUT / 'protocol_v2.json').read_text()) == json.loads(json.dumps(spec)), 'Frozen v2 config changed'
    else:
        OUT.mkdir(parents=True, exist_ok=True)
        assert not any((OUT / fw).exists() for fw in ['cv', 'loso']), 'OUT partially initialised without protocol_v2.json; clean manually'
        # stage the frozen 20260909 within-person covariances once, atomically (single-process prepare step)
        if not (OUT / 'covariances.json').exists() and (LOCKED / 'covariances.json').exists():
            tmp = OUT / 'covariances.npy.tmp'
            tmp.write_bytes((LOCKED / 'covariances.npy').read_bytes())
            tmp.rename(OUT / 'covariances.npy')
            (OUT / 'covariances.json').write_bytes((LOCKED / 'covariances.json').read_bytes())
        save_json(OUT / 'protocol_v2.json', spec)
        for name in [Path(__file__).name] + DEPENDENCIES:
            dest = OUT / 'source' / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes((BASE / name).read_bytes())
        for name in COHORTS:
            cc = c[c.subject_id.isin(q['cohorts'][name])].copy().reset_index(drop=True)
            ss = sp[sp.subject_id.isin(cc.subject_id)].copy()
            assert len(cc) == len(q['cohorts'][name])
            for (r, f), g in ss.groupby(['repeat', 'fold']):
                assert len(g) == len(cc) and g.subject_id.is_unique
                assert set(g.role) == {'train', 'validation', 'test'}
                for role, h in g.groupby('role'):
                    assert set(h.label) == {0, 1}
            assert ss[ss.role.eq('test')].groupby(['repeat', 'subject_id']).size().eq(1).all()
            for fw in ['cv', 'loso']:
                (OUT / fw / name).mkdir(parents=True)
                cc.to_csv(OUT / fw / name / 'cohort.csv', index=False)
                ss.to_csv(OUT / fw / name / 'splits.csv', index=False)
        save_json(OUT / 'status.json', dict(status='prepared'))
    return c


def covariance_cache(c):
    dest = OUT / 'covariances.npy'
    meta = OUT / 'covariances.json'
    if meta.exists():
        m = json.loads(meta.read_text())
        assert digest(dest) == m['sha256']
        assert m['ids'] == c.subject_id.tolist()
        return np.load(dest, mmap_mode='r')
    vm = json.loads((CACHE / 'verification.json').read_text())
    assert digest(CACHE / 'timeseries.npz') == vm['cache_sha256']
    assert vm['effective_sample_interval_seconds'] == 1.
    z = np.load(CACHE / 'timeseries.npz', allow_pickle=False)
    ids = z['subject_id'].astype(str)
    ix = {s: i for i, s in enumerate(ids)}
    data = z['data']
    offset = z['offsets']
    assert data.shape[1] == 424 and offset[-1] == len(data)
    cov = []
    for n, sid in enumerate(c.subject_id):
        i = ix[sid]
        d = np.asarray(data[offset[i]:offset[i + 1]], dtype=np.float64)
        assert d.ndim == 2 and np.isfinite(d).all()
        cov.append(LedoitWolf(store_precision=False).fit(d).covariance_)
        if n % 50 == 0:
            print('COVARIANCE', n, '/378', flush=True)
    z.close()
    arr = np.asarray(cov)
    assert arr.shape == (378, 424, 424)
    np.save(dest, arr)
    save_json(meta, dict(sha256=digest(dest), ids=c.subject_id.tolist(), source_sha256=vm['cache_sha256'],
                         scope='within-person only; no group fit'))
    return np.load(dest, mmap_mode='r')


def fit_mlp(name, x, y, tr, va, te, fold, seeds, folder, training):
    scores = {'validation': [], 'test': []}
    for seed in seeds:
        tag = name + '_seed' + str(seed)
        model, xt, info = train_neural(x, y, tr, va, fold, tag, folder, seed=seed)
        saved = torch.load(folder / f'fold{fold}_{tag}.pt', weights_only=True)
        replay = MLP(saved['input_features'])
        replay.load_state_dict(saved['state_dict'])
        for role, ixr in [('validation', va), ('test', te)]:
            p = predict(model, xt, ixr)
            np.testing.assert_allclose(predict(replay, xt, ixr), p, rtol=1e-6, atol=1e-7)
            scores[role].append(p)
        training.append(dict(model=tag, seed=seed, **info))
    return {role: np.mean(v, axis=0) for role, v in scores.items()}


def run_fold(c, vol, tiv, cov, tr, va, te, fold_id, seed_offset, folder):
    folder.mkdir(parents=True, exist_ok=True)
    assert not (set(tr) & set(va) or set(tr) & set(te) or set(va) & set(te))
    assert sorted(np.r_[tr, va, te].tolist()) == list(range(len(c)))
    y = c.label.to_numpy(np.int64)
    search, selection, training, scores = [], [], [], {}
    print(folder.name, 'geometry', len(tr), len(va), len(te), flush=True)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        mean = _geometric_mean(cov[tr], max_iter=100, tol=1e-8)
    white, logs = transform(cov, mean)
    residual = float(np.linalg.norm(logs[tr].mean(axis=0)) / mean.size)
    assert residual < 1e-7, f'Geometry residual {residual}'
    raw = sym_matrix_to_vec(logs, discard_diagonal=True).astype(np.float32)
    del logs
    tx, order, tscale = select_features(raw, y, tr)
    del raw
    sc = StandardScaler().fit(vol[tr])
    sx = sc.transform(vol).astype(np.float32)
    tsc = StandardScaler().fit(tiv[tr, None])
    tv = tsc.transform(tiv[:, None])
    ctrl, ctrlfit = controls(c, tr)
    dx, dfit = demographic(c, tr)
    full = np.c_[ctrl['site_motion_lr'], dx]
    joblib.dump(dict(mean=mean, white=white, order=order, tangent_scaler=tscale, structural_scaler=sc,
                     tiv_scaler=tsc, controls=ctrlfit, demographic=dfit, fit_ids=c.subject_id.iloc[tr].tolist()),
                folder / 'transforms.joblib')
    for name, x in [('structural_lr', sx), ('structural_tiv_lr', np.c_[sx, tv]), ('tiv_lr', tv),
                    ('full_covariates_lr', full), ('full_covariates_tiv_lr', np.c_[full, tv]), ('tangent_lr', tx)]:
        scores[name] = fit_lr(name, x, y, tr, va, te, folder, search)
    print(folder.name, 'neural', flush=True)
    seeds = [sb + seed_offset for sb in SEED_BASES]
    scores['structural_mlp'] = fit_mlp('structural_mlp', sx, y, tr, va, te, fold_id, seeds, folder, training)
    scores['tangent_mlp'] = fit_mlp('tangent_mlp', tx, y, tr, va, te, fold_id, seeds, folder, training)
    for name, base, added in [
        ('image_fusion_lr', 'tangent_lr', 'structural_lr'), ('image_fusion_mlp', 'tangent_mlp', 'structural_lr'),
        ('full_functional_lr', 'full_covariates_lr', 'tangent_lr'), ('full_functional_mlp', 'full_covariates_lr', 'tangent_mlp'),
        ('full_functional_tiv_mlp', 'full_covariates_tiv_lr', 'tangent_mlp'),
        ('full_fusion_lr', 'full_functional_lr', 'structural_lr'), ('full_fusion_mlp', 'full_functional_mlp', 'structural_lr'),
        ('full_fusion_tiv_mlp', 'full_functional_tiv_mlp', 'structural_lr'),
        ('full_fusion_structural_mlp', 'full_functional_mlp', 'structural_mlp')]:
        blend(name, base, added, scores, y[va], selection)
    assert set(scores) == set(MODEL_NAMES)
    for role, ixr in [('validation', va), ('test', te)]:
        rows = []
        for name, v in scores.items():
            p = v[role]
            assert np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all()
            rows.extend(dict(fold_id=fold_id, model=name, subject_id=c.subject_id.iloc[i], site=c.site.iloc[i],
                             y=int(y[i]), score=float(s)) for i, s in zip(ixr, p))
        pd.DataFrame(rows).to_csv(folder / (role + '.csv'), index=False)
    pd.DataFrame(search).to_csv(folder / 'C_search.csv', index=False)
    pd.DataFrame(selection).to_csv(folder / 'selection.csv', index=False)
    pd.DataFrame(training).to_csv(folder / 'training.csv', index=False)
    save_json(folder / 'audit.json', dict(residual=residual, geometry_warnings=[str(w.message) for w in caught],
              train_ids=c.subject_id.iloc[tr].tolist(), validation_ids=c.subject_id.iloc[va].tolist(),
              test_ids=c.subject_id.iloc[te].tolist(), checkpoint_replay_passed=True, diagnosis_used_for_qc=False))
    files = {p.name: digest(p) for p in folder.iterdir() if p.is_file() and p.name != 'complete.json'}
    save_json(folder / 'complete.json', dict(status='complete_replay_checked', files=files,
              protocol_sha256=digest(OUT / 'protocol_v2.json')))


def summarize_cv():
    root = OUT / 'cv'
    for cohort in COHORTS:
        folder = root / cohort
        cc = pd.read_csv(folder / 'cohort.csv')
        parts = [(r, f) for r in range(1, 6) for f in range(1, 4)]
        p = pd.concat([pd.read_csv(folder / f'repeat{r}_fold{f}/test.csv').assign(repeat=r, fold=f) for r, f in parts])
        assert len(p) == len(cc) * 5 * len(MODEL_NAMES) and not p.duplicated(['repeat', 'model', 'subject_id']).any()
        p.to_csv(folder / 'predictions.csv', index=False)
        rows = []
        for (r, f, m), g in p.groupby(['repeat', 'fold', 'model']):
            rows.append(dict(repeat=r, fold=f, model=m, n=len(g), auc=roc_auc_score(g.y, g.score),
                             within_site_auc=conditional_auc(g), ap=average_precision_score(g.y, g.score),
                             balanced_accuracy=balanced_accuracy_score(g.y, g.score >= .5), brier=brier_score_loss(g.y, g.score)))
        fm = pd.DataFrame(rows)
        fm.to_csv(folder / 'fold_metrics.csv', index=False)
        rm = fm.groupby(['repeat', 'model'])[['auc', 'within_site_auc', 'ap', 'balanced_accuracy', 'brier']].mean().reset_index()
        rm.to_csv(folder / 'repeat_metrics.csv', index=False)
        rm.groupby('model').agg(mean_auc=('auc', 'mean'), min_repeat_auc=('auc', 'min'), max_repeat_auc=('auc', 'max'),
                                within_site_auc=('within_site_auc', 'mean'), mean_ap=('ap', 'mean'),
                                mean_brier=('brier', 'mean')).to_csv(folder / 'summary.csv')
    save_json(root / 'status.json', dict(status='complete_replay_checked', framework='cv', folds=45,
                                         models_per_fold=len(MODEL_NAMES)))


def summarize_loso():
    root = OUT / 'loso'
    for cohort in COHORTS:
        folder = root / cohort
        cc = pd.read_csv(folder / 'cohort.csv')
        present = [s for s in SITES if (folder / f'site_{s}' / 'test.csv').exists()]
        p = pd.concat([pd.read_csv(folder / f'site_{s}/test.csv') for s in present])
        assert len(p) == len(cc) * len(MODEL_NAMES) and not p.duplicated(['model', 'subject_id']).any()
        p.to_csv(folder / 'predictions.csv', index=False)
        rows = []
        for (s, m), g in p.groupby(['site', 'model']):
            pairs = int(g.y.sum() * (len(g) - g.y.sum()))
            rows.append(dict(site=s, model=m, n=len(g), pos=int(g.y.sum()), pairs=pairs,
                             auc=roc_auc_score(g.y, g.score) if pairs else np.nan))
        sm = pd.DataFrame(rows)
        sm.to_csv(folder / 'site_metrics.csv', index=False)
        srows = []
        for m, g in sm.groupby('model'):
            gv = g.dropna(subset=['auc'])
            pw = float((gv.auc * gv.pairs).sum() / gv.pairs.sum())
            macro = float(gv.auc.mean())
            big = gv[gv.n >= 20]
            pooled = float(roc_auc_score(p[p.model.eq(m)].y, p[p.model.eq(m)].score))
            srows.append(dict(model=m, pair_weighted_auc=pw, macro_auc=macro, pooled_auc=pooled,
                              pair_weighted_auc_drop_small=float((big.auc * big.pairs).sum() / big.pairs.sum()),
                              macro_auc_drop_small=float(big.auc.mean()), n_sites=len(gv)))
        pd.DataFrame(srows).to_csv(folder / 'summary.csv', index=False)
    save_json(root / 'status.json', dict(status='complete_replay_checked', framework='loso', sites=SITES,
                                         models_per_site=len(MODEL_NAMES)))


def inner_holdout(cc, keep_idx, site_index):
    strata = (cc.site.astype(str) + '__' + cc.label.astype(int).astype(str)).to_numpy()[keep_idx]
    tr, va = train_test_split(np.asarray(keep_idx), test_size=0.15, stratify=strata, random_state=2026 + site_index)
    return np.sort(tr), np.sort(va)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--framework', choices=['cv', 'loso'], required=True)
    ap.add_argument('--prepare-only', action='store_true')
    args = ap.parse_args()
    c0 = prepare()
    if args.prepare_only:
        print('PREPARED', OUT, flush=True)
        return
    fw = args.framework
    root = OUT / fw
    try:
        torch.set_num_threads(4)
        with threadpool_limits(limits=4):
            cov0 = covariance_cache(c0)
            z = np.load(VOL, allow_pickle=False)
            vi = {s: i for i, s in enumerate(z['subject_id'].astype(str))}
            ci = {s: i for i, s in enumerate(c0.subject_id)}
            done = 0
            for cohort in COHORTS:
                folder = root / cohort
                c = pd.read_csv(folder / 'cohort.csv')
                sp = pd.read_csv(folder / 'splits.csv')
                cov = np.asarray(cov0[[ci[s] for s in c.subject_id]])
                ixv = [vi[s] for s in c.subject_id]
                vol = z['volume_fractions'][ixv]
                tiv = z['total_intracranial_mm3'][ixv]
                assert vol.shape == (len(c), 98) and np.isfinite(vol).all()
                lookup = {sid: i for i, sid in enumerate(c.subject_id)}
                if fw == 'cv':
                    jobs = []
                    for r in range(1, 6):
                        for f in range(1, 4):
                            g = sp[sp.repeat.eq(r) & sp.fold.eq(f)]
                            idx = {role: np.array([lookup[s] for s in g[g.role.eq(role)].subject_id])
                                   for role in ['train', 'validation', 'test']}
                            jobs.append((f'repeat{r}_fold{f}', idx['train'], idx['validation'], idx['test'], f, f * 10 + r))
                else:
                    site_arr = c.site.astype(str).to_numpy()
                    jobs = []
                    for si, s in enumerate(SITES):
                        te = np.where(site_arr == s)[0]
                        keep = np.where(site_arr != s)[0]
                        if len(te) == 0 or len(set(c.label.to_numpy()[te])) < 2:
                            print('SKIP site', s, 'cohort', cohort, '(<2 classes or empty)', flush=True)
                            continue
                        tr, va = inner_holdout(c, keep, si)
                        jobs.append((f'site_{s}', tr, va, te, si + 1, si))
                for tag, tr, va, te, fold_id, seed_off in jobs:
                    dest = folder / tag
                    if (dest / 'complete.json').exists():
                        meta = json.loads((dest / 'complete.json').read_text())
                        assert meta['protocol_sha256'] == digest(OUT / 'protocol_v2.json')
                        for file, h in meta['files'].items():
                            assert digest(dest / file) == h
                    else:
                        save_json(root / 'status.json', dict(status='running', framework=fw, cohort=cohort,
                                  unit=tag, completed=done, updated=time.strftime('%Y-%m-%d %H:%M:%S')))
                        run_fold(c, vol, tiv, cov, tr, va, te, fold_id, seed_off, dest)
                    done += 1
                    print('UNIT COMPLETE', fw, done, tag, 'metrics withheld', flush=True)
            (summarize_cv if fw == 'cv' else summarize_loso)()
        print('COMPLETE', fw, OUT, flush=True)
    except BaseException as e:
        save_json(root / 'status.json', dict(status='failed', framework=fw, error=repr(e)))
        traceback.print_exc()
        raise


if __name__ == '__main__':
    main()
