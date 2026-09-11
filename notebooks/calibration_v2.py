"""Analysis v2 calibration (pre-registration section 8). Reliability bins, ECE,
Brier and Brier skill score for the four report models, per cohort, on pooled
mixed-site test-fold predictions. Pure numpy/pandas; runs on the server.
"""
from pathlib import Path
import json, argparse
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
OUT = BASE / 'runs/structural_fusion_v2_20260910'
COHORTS = ['primary', 'warning_free', 'include_holds']
MODELS = ['full_covariates_lr', 'full_functional_mlp', 'full_fusion_structural_mlp', 'image_fusion_mlp']
N_BINS = 10


def reliability(y, p, nbins=N_BINS):
    y = np.asarray(y, float); p = np.asarray(p, float)
    order = np.argsort(p)
    y, p = y[order], p[order]
    edges = np.linspace(0, len(p), nbins + 1).astype(int)
    rows, ece = [], 0.0
    for b in range(nbins):
        lo, hi = edges[b], edges[b + 1]
        if hi <= lo:
            continue
        mp = float(p[lo:hi].mean()); of = float(y[lo:hi].mean()); n = hi - lo
        ece += (n / len(p)) * abs(mp - of)
        rows.append(dict(bin=b, n=int(n), mean_pred=mp, obs_freq=of))
    return rows, float(ece)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', type=Path, default=OUT / 'v2_stats'); a = ap.parse_args()
    st = json.loads((OUT / 'cv' / 'status.json').read_text())
    assert st['status'] == 'complete_replay_checked', st
    a.out.mkdir(parents=True, exist_ok=True)
    bin_rows, summ_rows = [], []
    for cohort in COHORTS:
        p = pd.read_csv(OUT / 'cv' / cohort / 'predictions.csv')
        for model in MODELS:
            g = p[p.model == model]
            y = g.y.to_numpy(); s = g.score.to_numpy()
            prev = float(y.mean())
            brier = float(np.mean((s - y) ** 2))
            brier_ref = prev * (1 - prev)
            bss = float(1 - brier / brier_ref) if brier_ref > 0 else np.nan
            rows, ece = reliability(y, s)
            for r in rows:
                bin_rows.append(dict(cohort=cohort, model=model, **r))
            summ_rows.append(dict(cohort=cohort, model=model, n=len(y), prevalence=prev,
                                  ece=ece, brier=brier, brier_ref=brier_ref, brier_skill_score=bss))
    pd.DataFrame(bin_rows).to_csv(a.out / 'calibration.csv', index=False)
    pd.DataFrame(summ_rows).to_csv(a.out / 'calibration_summary.csv', index=False)
    print(pd.DataFrame(summ_rows).round(4).to_string(index=False))
    print('\nPre-registered statement: all model outputs are class-weighted and uncalibrated; '
          'they must not be read as individual diagnostic risk regardless of ECE.')


if __name__ == '__main__':
    main()
