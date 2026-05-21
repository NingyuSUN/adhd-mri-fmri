"""
utils/metrics.py
Evaluation helpers: bootstrap AUC CI, subject-level aggregation.
"""

import numpy as np
from sklearn.metrics import roc_auc_score


def bootstrap_auc_ci(y_true, y_score, n_boot: int = 2000, seed: int = 42):
    """
    Bootstrap 95% CI for AUC.

    Args:
        y_true: binary ground-truth labels.
        y_score: predicted probabilities.
        n_boot: number of bootstrap resamples.
        seed: random seed for reproducibility.

    Returns:
        (mean_auc, ci_lower, ci_upper)
    """
    rng = np.random.default_rng(seed)
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    n = len(y_true)
    aucs = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        if len(np.unique(y_true[idx])) < 2:
            continue
        aucs.append(roc_auc_score(y_true[idx], y_score[idx]))
    if not aucs:
        return float("nan"), float("nan"), float("nan")
    aucs = np.array(aucs)
    return float(np.mean(aucs)), float(np.percentile(aucs, 2.5)), float(np.percentile(aucs, 97.5))


def aggregate_subject_auc(sub_ids, y_slice, p_slice):
    """
    Aggregate slice-level predictions to subject level (mean pooling).

    Args:
        sub_ids: array of subject IDs, one per slice.
        y_slice: binary labels, one per slice.
        p_slice: predicted probabilities, one per slice.

    Returns:
        (subject_auc, y_true_subjects, y_prob_subjects)
    """
    import pandas as pd
    df = pd.DataFrame({"sub_id": sub_ids, "y": y_slice, "p": p_slice})
    subj = df.groupby("sub_id").agg(y=("y", "first"), p=("p", "mean")).reset_index()
    auc = roc_auc_score(subj["y"].values, subj["p"].values)
    return auc, subj["y"].values, subj["p"].values
