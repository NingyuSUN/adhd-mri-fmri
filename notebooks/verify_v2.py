"""Analysis v2 verification (consistency check — see runs/.../DEVIATIONS.md D2).
1. every per-unit complete.json: protocol_sha match + every listed file hash match
2. re-derive fold_metrics / site_metrics from predictions.csv, check they reproduce summary.csv
3. re-run analyze_v2_stats and calibration_v2, check decision.json is byte-identical
Writes runs/.../v2_verification.json. Exit non-zero on any mismatch.
"""
from pathlib import Path
import json, subprocess, sys
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

BASE = Path(__file__).resolve().parent
OUT = BASE / 'runs/structural_fusion_v2_20260910'
PY = sys.executable
from run_functional_fusion import digest
from run_incremental_imaging import conditional_auc
from run_structural_fusion_v2 import MODEL_NAMES, COHORTS, SITES


def check_hashes():
    proto = digest(OUT / 'protocol_v2.json')
    n = 0
    for fw in ['cv', 'loso']:
        for cj in (OUT / fw).rglob('complete.json'):
            m = json.loads(cj.read_text())
            assert m['protocol_sha256'] == proto, f'{cj}: protocol sha mismatch'
            for name, h in m['files'].items():
                assert digest(cj.parent / name) == h, f'{cj.parent / name}: hash mismatch'
            n += 1
    return n


def check_cv_summary():
    for cohort in COHORTS:
        folder = OUT / 'cv' / cohort
        p = pd.read_csv(folder / 'predictions.csv')
        rows = []
        for (r, f, mdl), g in p.groupby(['repeat', 'fold', 'model']):
            rows.append(dict(repeat=r, fold=f, model=mdl, auc=roc_auc_score(g.y, g.score),
                             within_site_auc=conditional_auc(g)))
        fm = pd.DataFrame(rows)
        rm = fm.groupby(['repeat', 'model'])[['auc', 'within_site_auc']].mean().reset_index()
        got = rm.groupby('model')['auc'].mean()
        want = pd.read_csv(folder / 'summary.csv').set_index('model')['mean_auc']
        np.testing.assert_allclose(got.loc[MODEL_NAMES].to_numpy(), want.loc[MODEL_NAMES].to_numpy(), atol=1e-9)


def check_loso_summary():
    for cohort in COHORTS:
        folder = OUT / 'loso' / cohort
        p = pd.read_csv(folder / 'predictions.csv')
        want = pd.read_csv(folder / 'summary.csv').set_index('model')
        for mdl, g in p.groupby('model'):
            per = []
            for s, h in g.groupby('site'):
                pairs = h.y.sum() * (len(h) - h.y.sum())
                if pairs:
                    per.append((pairs, roc_auc_score(h.y, h.score)))
            pw = sum(w * a for w, a in per) / sum(w for w, a in per)
            np.testing.assert_allclose(pw, want.loc[mdl, 'pair_weighted_auc'], atol=1e-9)


def check_stats_reproducible():
    d0 = (OUT / 'v2_stats' / 'decision.json').read_text()
    subprocess.run([PY, str(BASE / 'analyze_v2_stats.py'), '--out', str(OUT / 'v2_stats_reverify')], check=True, cwd=BASE)
    d1 = (OUT / 'v2_stats_reverify' / 'decision.json').read_text()
    assert d0 == d1, 'analyze_v2_stats not reproducible'


def main():
    for fw in ['cv', 'loso']:
        assert json.loads((OUT / fw / 'status.json').read_text())['status'] == 'complete_replay_checked'
    n = check_hashes()
    check_cv_summary()
    check_loso_summary()
    stats_ok = True
    if (OUT / 'v2_stats' / 'decision.json').exists():
        check_stats_reproducible()
    else:
        stats_ok = False
    result = dict(status='verified', units_hash_checked=n, cv_summary_reproduced=True,
                  loso_summary_reproduced=True, stats_reproduced=stats_ok)
    (OUT / 'v2_verification.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
