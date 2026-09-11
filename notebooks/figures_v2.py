"""Analysis v2 figures (pre-registration section 9). Runs locally (matplotlib).
Reads the v2_stats CSVs (pull from server first). Writes 3 PNGs.

  F1  per-site ΔAUC forest plot, primary contrast P, LOSO, one row-group per cohort
  F2  mean AUC bar chart, confound baseline vs imaging/fusion models, primary cohort, CV
  F3  reliability curves, 4 report models, primary cohort
"""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

COHORTS = ['primary', 'warning_free', 'include_holds']
BAR_ORDER = ['full_covariates_tiv_lr', 'full_covariates_lr', 'full_functional_tiv_mlp', 'full_functional_mlp',
             'full_fusion_structural_mlp', 'full_fusion_mlp', 'image_fusion_mlp', 'tangent_mlp', 'structural_mlp', 'tiv_lr']
CAL_MODELS = ['full_covariates_lr', 'full_functional_mlp', 'full_fusion_structural_mlp', 'image_fusion_mlp']


def f1_forest(stats_dir, fig_dir):
    d = pd.read_csv(stats_dir / 'loso_per_site_deltas.csv')
    d = d[d.contrast == 'P'].copy()
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharex=True)
    for ax, cohort in zip(axes, COHORTS):
        g = d[d.cohort == cohort].sort_values('n')
        yy = np.arange(len(g))
        ax.errorbar(g.delta, yy, xerr=[g.delta - g.ci95_lo, g.ci95_hi - g.delta], fmt='o', capsize=3, color='#333')
        ax.axvline(0, color='#999', lw=1)
        ax.axvspan(-0.02, 0.02, color='#4c78a8', alpha=0.12)
        ax.set_yticks(yy); ax.set_yticklabels([f'{s} (n={n})' for s, n in zip(g.site, g.n)], fontsize=8)
        ax.set_title(f'{cohort}', fontsize=10)
        ax.set_xlabel('ΔAUC  (structural-MLP fusion − functional MLP)')
    fig.suptitle('F1  Per-site held-out ΔAUC, primary contrast, strict LOSO (95% within-site subject bootstrap)', fontsize=11)
    fig.tight_layout()
    fig.savefig(fig_dir / 'v2_F1_loso_forest.png', dpi=150)
    plt.close(fig)


def f2_bars(stats_dir, fig_dir):
    s = pd.read_csv(stats_dir / 'cv_primary_summary.csv').set_index('model')
    models = [m for m in BAR_ORDER if m in s.index]
    y = s.loc[models, 'mean_auc'].to_numpy()
    lo = y - s.loc[models, 'min_repeat_auc'].to_numpy()
    hi = s.loc[models, 'max_repeat_auc'].to_numpy() - y
    fig, ax = plt.subplots(figsize=(9, 4.5))
    colors = ['#54a24b' if m.startswith('full_covariates') else '#4c78a8' if m.startswith('full_') else '#e45756' for m in models]
    ax.bar(range(len(models)), y, yerr=[lo, hi], capsize=3, color=colors)
    ax.axhline(0.5, color='#999', lw=1, ls='--')
    ax.set_xticks(range(len(models))); ax.set_xticklabels(models, rotation=40, ha='right', fontsize=8)
    ax.set_ylabel('mean AUC (5 repeats)'); ax.set_ylim(0.45, 0.78)
    ax.set_title('F2  Mixed-site CV mean AUC, cohort primary  '
                 '(green = non-imaging control, blue = +confounds, red = image-only)', fontsize=10)
    fig.tight_layout(); fig.savefig(fig_dir / 'v2_F2_cv_bars.png', dpi=150); plt.close(fig)


def f3_reliability(stats_dir, fig_dir):
    c = pd.read_csv(stats_dir / 'calibration.csv')
    c = c[c.cohort == 'primary']
    fig, ax = plt.subplots(figsize=(5.2, 5))
    ax.plot([0, 1], [0, 1], color='#999', lw=1, ls='--', label='perfect')
    for m in CAL_MODELS:
        g = c[c.model == m].sort_values('mean_pred')
        ax.plot(g.mean_pred, g.obs_freq, 'o-', ms=4, label=m)
    ax.set_xlabel('mean predicted probability'); ax.set_ylabel('observed frequency')
    ax.set_title('F3  Reliability curves, cohort primary (pooled CV test folds)', fontsize=10)
    ax.legend(fontsize=8); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    fig.tight_layout(); fig.savefig(fig_dir / 'v2_F3_reliability.png', dpi=150); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stats-dir', type=Path, required=True, help='pulled v2_stats/ dir (contains the CSVs)')
    ap.add_argument('--fig-dir', type=Path, default=None)
    a = ap.parse_args()
    fig_dir = a.fig_dir or (a.stats_dir / 'figures')
    fig_dir.mkdir(parents=True, exist_ok=True)
    f1_forest(a.stats_dir, fig_dir)
    f2_bars(a.stats_dir, fig_dir)
    f3_reliability(a.stats_dir, fig_dir)
    print('WROTE', fig_dir)


if __name__ == '__main__':
    main()
