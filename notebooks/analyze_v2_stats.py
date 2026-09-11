"""Analysis v2 statistics: Nadeau-Bengio corrected CV intervals, site-stratified
subject bootstrap for LOSO, TOST equivalence + pre-registered 4-branch decision.
Pre-registration: docs/analysis_v2_protocol.md sections 6-7. Reads only the frozen
v2 prediction outputs; produces no model. Deterministic (fixed bootstrap seed).
"""
from pathlib import Path
import json, argparse
import numpy as np
import pandas as pd
from scipy import stats

BASE = Path(__file__).resolve().parent
OUT = BASE / 'runs/structural_fusion_v2_20260910'
COHORTS = ['primary', 'warning_free', 'include_holds']
CONTRASTS = [
    ('P',  'full_fusion_structural_mlp', 'full_functional_mlp'),
    ('S1', 'full_functional_mlp', 'full_covariates_lr'),
    ('S2', 'full_fusion_mlp', 'full_functional_mlp'),
    ('S3', 'full_fusion_lr', 'full_functional_lr'),
    ('S4', 'image_fusion_mlp', 'tangent_mlp'),
    ('S5', 'full_fusion_tiv_mlp', 'full_functional_tiv_mlp'),
    ('E1', 'structural_mlp', 'structural_lr'),
]
MARGIN = 0.02
N_BOOT = 10000
BOOT_SEED = 20260910


def fast_auc(y, s):
    """Mann-Whitney U AUC. y in {0,1}. Returns nan if a class is absent."""
    y = np.asarray(y); s = np.asarray(s)
    n1 = int(y.sum()); n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return np.nan
    r = stats.rankdata(s)
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def boot_aucs(y, s, idx):
    """Vectorised bootstrap AUC. y,s: (n,); idx: (B,n) resample indices -> (B,) AUCs.
    Continuous float scores: ties assumed absent (average-rank correction omitted)."""
    ys = y[idx].astype(np.int64)                       # (B,n)
    ss = s[idx]                                        # (B,n)
    B, n = idx.shape
    n1 = ys.sum(1); n0 = n - n1                        # (B,)
    order = np.argsort(ss, axis=1, kind='stable')      # (B,n)
    ranks = np.empty((B, n), dtype=np.float64)
    np.put_along_axis(ranks, order, np.broadcast_to(np.arange(1, n + 1, dtype=np.float64), (B, n)), axis=1)
    rank_sum_pos = (ranks * ys).sum(1)                 # (B,)
    with np.errstate(invalid='ignore', divide='ignore'):
        auc = (rank_sum_pos - n1 * (n1 + 1) / 2) / (n1 * n0)
    auc[(n1 == 0) | (n0 == 0)] = np.nan
    return auc


# ---------- 6A: mixed-site CV, Nadeau-Bengio corrected variance ----------
def nb_interval(deltas):
    d = np.asarray(deltas, float)
    n = len(d)                       # 15 = r*k
    mean = float(d.mean())
    var_raw = float(d.var(ddof=1))
    corr = 1.0 / n + 0.5             # 1/(r*k) + n_test/n_train, n_test/n_train = (1/3)/(2/3)
    se = float(np.sqrt(corr * var_raw))
    out = {'mean': mean, 'se_nb': se, 'n': n}
    for tag, df in [('', n - 1), ('_conservative', 2)]:   # df = r*k-1 = 14 ; df = k-1 = 2
        t = float(stats.t.ppf(0.95, df))
        out[f'ci_lo{tag}'] = mean - t * se
        out[f'ci_hi{tag}'] = mean + t * se
    return out


def cv_stats():
    rows = []
    for cohort in COHORTS:
        fm = pd.read_csv(OUT / 'cv' / cohort / 'fold_metrics.csv')
        for metric in ['auc', 'within_site_auc']:
            wide = fm.pivot_table(index=['repeat', 'fold'], columns='model', values=metric)
            for cid, cand, ref in CONTRASTS:
                d = (wide[cand] - wide[ref]).to_numpy()
                assert len(d) == 15
                r = nb_interval(d)
                rows.append(dict(cohort=cohort, contrast=cid, candidate=cand, reference=ref, metric=metric,
                                 mean_delta=r['mean'], se_nb=r['se_nb'],
                                 ci90_lo=r['ci_lo'], ci90_hi=r['ci_hi'],
                                 ci90_lo_df2=r['ci_lo_conservative'], ci90_hi_df2=r['ci_hi_conservative'],
                                 positive_of_15=int((d > 1e-12).sum()), negative_of_15=int((d < -1e-12).sum())))
    return pd.DataFrame(rows)


# ---------- 6B: LOSO, site-stratified subject bootstrap ----------
def loso_stats():
    summary_rows, site_rows = [], []
    for cohort in COHORTS:
        p = pd.read_csv(OUT / 'loso' / cohort / 'predictions.csv')
        sites = sorted(p.site.unique())
        # per (site, model) arrays
        by = {}
        for (s, m), g in p.groupby(['site', 'model']):
            by[(s, m)] = (g.y.to_numpy(), g.score.to_numpy(), g.subject_id.to_numpy())
        for cid, cand, ref in CONTRASTS:
            per_site_pairs, per_site_delta = {}, {}
            for s in sites:
                yc, sc, _ = by[(s, cand)]
                yr, sr, _ = by[(s, ref)]
                assert np.array_equal(yc, yr)
                pairs = int(yc.sum() * (len(yc) - yc.sum()))
                per_site_pairs[s] = pairs
                per_site_delta[s] = fast_auc(yc, sc) - fast_auc(yr, sr) if pairs else np.nan
            # point estimates
            def summ(keys):
                dv = np.array([per_site_delta[s] for s in keys]); wv = np.array([per_site_pairs[s] for s in keys], float)
                ok = ~np.isnan(dv)
                pw = float((dv[ok] * wv[ok]).sum() / wv[ok].sum())
                macro = float(np.nanmean(dv))
                return pw, macro
            big = [s for s in sites if len(by[(s, cand)][0]) >= 20]
            pw_all, macro_all = summ(sites)
            pw_big, macro_big = summ(big)
            # bootstrap: sites held fixed; resample subjects within each site (vectorised over B)
            rng = np.random.default_rng(BOOT_SEED)
            boot_delta = np.full((len(sites), N_BOOT), np.nan)   # per-site Δ over B resamples
            boot_pairs = np.zeros((len(sites), N_BOOT))
            for si, s in enumerate(sites):
                yc, sc, _ = by[(s, cand)]
                yr, sr, _ = by[(s, ref)]
                n = len(yc)
                idx = rng.integers(0, n, (N_BOOT, n))
                ac = boot_aucs(yc, sc, idx)
                ar = boot_aucs(yr, sr, idx)
                yb = yc[idx]
                pr = yb.sum(1) * (n - yb.sum(1))
                boot_delta[si] = ac - ar
                boot_pairs[si] = pr
            ok = ~np.isnan(boot_delta)
            num = np.where(ok, boot_delta * boot_pairs, 0.0).sum(0)
            den = np.where(ok, boot_pairs, 0.0).sum(0)
            with np.errstate(invalid='ignore', divide='ignore'):
                boot_pw = num / den
            boot_macro = np.nanmean(boot_delta, axis=0)
            for metric, point, arr in [('pair_weighted', pw_all, boot_pw), ('macro', macro_all, boot_macro)]:
                lo, hi = np.nanpercentile(arr, [5, 95])
                summary_rows.append(dict(cohort=cohort, contrast=cid, candidate=cand, reference=ref,
                                         metric=metric, point=point, ci90_lo=float(lo), ci90_hi=float(hi)))
            summary_rows.append(dict(cohort=cohort, contrast=cid, candidate=cand, reference=ref,
                                     metric='pair_weighted_drop_small', point=pw_big, ci90_lo=np.nan, ci90_hi=np.nan))
            summary_rows.append(dict(cohort=cohort, contrast=cid, candidate=cand, reference=ref,
                                     metric='macro_drop_small', point=macro_big, ci90_lo=np.nan, ci90_hi=np.nan))
            # per-site delta + within-site subject bootstrap 95% CI
            for si, s in enumerate(sites):
                yc, sc, _ = by[(s, cand)]; yr, sr, _ = by[(s, ref)]
                n = len(yc)
                rng2 = np.random.default_rng(BOOT_SEED + 1 + si)
                idx = rng2.integers(0, n, (2000, n))
                bd = boot_aucs(yc, sc, idx) - boot_aucs(yr, sr, idx)
                lo, hi = np.nanpercentile(bd, [2.5, 97.5])
                site_rows.append(dict(cohort=cohort, contrast=cid, site=s, n=len(yc), pos=int(yc.sum()),
                                      pairs=per_site_pairs[s], delta=per_site_delta[s],
                                      ci95_lo=float(lo), ci95_hi=float(hi)))
    return pd.DataFrame(summary_rows), pd.DataFrame(site_rows)


# ---------- 6C / 7: TOST + 4-branch decision ----------
def branch(lo, hi):
    m = MARGIN
    if lo >= -m and hi <= m:
        return 'B1_bounded_null'
    if lo > 0 and hi > m:
        return 'B2_meaningful_increment'
    if hi < -m:
        return 'B3_meaningful_decrement'
    return 'B4_inconclusive_underpowered'


WORDING = {
    'B1_bounded_null': 'Adding structural MRI to the confound + functional pipeline does not produce a methodologically meaningful AUC increment: the paired delta is equivalent to zero to within +/-0.02 AUC.',
    'B2_meaningful_increment': 'A methodologically meaningful positive increment cannot be ruled out and the estimate is positive; audit for leakage / confound imbalance before any positive claim.',
    'B3_meaningful_decrement': 'Adding imaging meaningfully lowered AUC; investigate added-modality overfitting or alpha-selection instability.',
    'B4_inconclusive_underpowered': 'The data cannot establish equivalence: the 90% interval extends beyond +/-0.02. Point estimate reported; a small effect in the crossed direction cannot be excluded.',
}


def decide(cv_df, loso_df):
    out = {'margin': MARGIN, 'primary_contrast': 'P (full_fusion_structural_mlp - full_functional_mlp)', 'cohort': 'primary', 'frameworks': {}}
    cv = cv_df[(cv_df.contrast == 'P') & (cv_df.cohort == 'primary') & (cv_df.metric == 'auc')].iloc[0]
    out['frameworks']['cv'] = dict(lo=float(cv.ci90_lo), hi=float(cv.ci90_hi), point=float(cv.mean_delta),
                                   branch=branch(cv.ci90_lo, cv.ci90_hi))
    lo_ = loso_df[(loso_df.contrast == 'P') & (loso_df.cohort == 'primary') & (loso_df.metric == 'pair_weighted')].iloc[0]
    out['frameworks']['loso'] = dict(lo=float(lo_.ci90_lo), hi=float(lo_.ci90_hi), point=float(lo_.point),
                                     branch=branch(lo_.ci90_lo, lo_.ci90_hi))
    b_cv = out['frameworks']['cv']['branch']; b_lo = out['frameworks']['loso']['branch']
    if b_cv == 'B1_bounded_null' and b_lo == 'B1_bounded_null':
        out['verdict'] = 'PRIMARY CLAIM CONFIRMED: bounded null under both mixed-site CV and strict LOSO.'
    elif 'B2_meaningful_increment' in (b_cv, b_lo):
        out['verdict'] = 'FALSIFICATION TRIGGERED in at least one framework: audit before interpreting.'
    elif b_cv == 'B1_bounded_null' and b_lo == 'B4_inconclusive_underpowered':
        out['verdict'] = 'Bounded null within-dataset (CV); cross-site transport underpowered (LOSO). No unqualified equivalence claim.'
    elif b_lo == 'B1_bounded_null' and b_cv == 'B4_inconclusive_underpowered':
        out['verdict'] = 'Bounded null under LOSO; mixed-site CV underpowered. No unqualified equivalence claim.'
    else:
        out['verdict'] = f'Neither framework confirms: CV={b_cv}, LOSO={b_lo}. Report point estimates and interval bounds; conclusion downgraded.'
    out['cv_wording'] = WORDING[b_cv]
    out['loso_wording'] = WORDING[b_lo]
    # descriptive for S1 (H2)
    s1cv = cv_df[(cv_df.contrast == 'S1') & (cv_df.cohort == 'primary') & (cv_df.metric == 'auc')].iloc[0]
    s1lo = loso_df[(loso_df.contrast == 'S1') & (loso_df.cohort == 'primary') & (loso_df.metric == 'pair_weighted')].iloc[0]
    out['H2_functional_vs_confound'] = dict(cv_branch=branch(s1cv.ci90_lo, s1cv.ci90_hi), cv_point=float(s1cv.mean_delta),
                                            loso_branch=branch(s1lo.ci90_lo, s1lo.ci90_hi), loso_point=float(s1lo.point))
    return out


def report(cv_df, loso_df, dec):
    L = ['# Analysis v2 — statistics (pre-registered)', '',
         'Pre-registration: `docs/analysis_v2_protocol.md` sections 6-7. Bootstrap seed '
         f'{BOOT_SEED}, {N_BOOT} resamples (site-stratified subject resampling; sites held fixed).', '',
         '## Primary contrast P: `full_fusion_structural_mlp` - `full_functional_mlp`, cohort `primary`', '',
         f"- Mixed-site CV (Nadeau-Bengio, df=14): Δ = {dec['frameworks']['cv']['point']:+.4f}, "
         f"90% CI [{dec['frameworks']['cv']['lo']:+.4f}, {dec['frameworks']['cv']['hi']:+.4f}] → **{dec['frameworks']['cv']['branch']}**",
         f"- Strict LOSO (pair-weighted, subject bootstrap): Δ = {dec['frameworks']['loso']['point']:+.4f}, "
         f"90% CI [{dec['frameworks']['loso']['lo']:+.4f}, {dec['frameworks']['loso']['hi']:+.4f}] → **{dec['frameworks']['loso']['branch']}**",
         '', f"### Verdict: {dec['verdict']}", '',
         f"- CV: {dec['cv_wording']}", f"- LOSO: {dec['loso_wording']}", '',
         f"### H2 (functional vs confound baseline, S1, primary): CV {dec['H2_functional_vs_confound']['cv_branch']} "
         f"(Δ {dec['H2_functional_vs_confound']['cv_point']:+.4f}); LOSO {dec['H2_functional_vs_confound']['loso_branch']} "
         f"(Δ {dec['H2_functional_vs_confound']['loso_point']:+.4f})", '',
         '## All contrasts — mixed-site CV (metric=auc)', '',
         '| cohort | contrast | Δ mean | 90% CI (df14) | 90% CI (df2) | +/15 |', '|---|---|---:|---|---|---:|']
    for _, r in cv_df[cv_df.metric == 'auc'].iterrows():
        L.append(f"| {r.cohort} | {r.contrast} | {r.mean_delta:+.4f} | "
                 f"[{r.ci90_lo:+.4f}, {r.ci90_hi:+.4f}] | [{r.ci90_lo_df2:+.4f}, {r.ci90_hi_df2:+.4f}] | {int(r.positive_of_15)} |")
    L += ['', '## All contrasts — strict LOSO (pair-weighted AUC)', '',
          '| cohort | contrast | Δ point | 90% CI (boot) | Δ drop-small |', '|---|---|---:|---|---:|']
    for _, r in loso_df[loso_df.metric == 'pair_weighted'].iterrows():
        ds = loso_df[(loso_df.cohort == r.cohort) & (loso_df.contrast == r.contrast) & (loso_df.metric == 'pair_weighted_drop_small')].iloc[0].point
        L.append(f"| {r.cohort} | {r.contrast} | {r.point:+.4f} | [{r.ci90_lo:+.4f}, {r.ci90_hi:+.4f}] | {ds:+.4f} |")
    L += ['', '## Notes', '',
          '- Δ = candidate − reference. Positive = imaging helps.',
          '- CV interval: Nadeau & Bengio (2003) corrected resampled t; correction = 1/15 + 0.5; df = r·k−1 = 14 '
          '(df = k−1 = 2 shown as conservative sensitivity). Bouckaert & Frank (2004) for df.',
          '- LOSO interval: site-stratified subject bootstrap (7 sites held fixed). Cluster bootstrap over 7 sites '
          'was rejected in review as invalid. Per-site Δ and within-site CIs in `loso_per_site_deltas.csv` (forest plot F1).',
          '- Repeat range / positive-fold counts are descriptive, not tests.',
          '- No family-wise correction across the 7 contrasts × 3 cohorts: they are same-direction consistency checks, '
          'and all-≤0 observed Δ means multiplicity would inflate false positives, not false nulls. Any Δ CI excluding '
          '0 on the positive side is flagged.']
    return '\n'.join(L)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', type=Path, default=OUT / 'v2_stats'); a = ap.parse_args()
    for fw in ['cv', 'loso']:
        st = json.loads((OUT / fw / 'status.json').read_text())
        assert st['status'] == 'complete_replay_checked', f'{fw} not complete: {st}'
    a.out.mkdir(parents=True, exist_ok=True)
    cv_df = cv_stats(); cv_df.to_csv(a.out / 'cv_contrast_stats.csv', index=False)
    loso_df, site_df = loso_stats()
    loso_df.to_csv(a.out / 'loso_contrast_stats.csv', index=False)
    site_df.to_csv(a.out / 'loso_per_site_deltas.csv', index=False)
    dec = decide(cv_df, loso_df)
    (a.out / 'decision.json').write_text(json.dumps(dec, indent=2))
    (a.out / 'REPORT_stats.md').write_text(report(cv_df, loso_df, dec), encoding='utf-8')
    print('WROTE', a.out)
    print(json.dumps(dec, indent=2))


if __name__ == '__main__':
    main()
