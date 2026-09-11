# Analysis v2 — confirmatory statistics, and why strict LOSO is not the primary endpoint

Pre-registration: [`analysis_v2_protocol.md`](analysis_v2_protocol.md) (finalized after an
independent methods/statistics review). Deviations: [`analysis_v2_deviations.md`](analysis_v2_deviations.md).
Independent consistency verification (`notebooks/verify_v2.py`): **verified** — 66 units
(45 mixed-site CV folds + 21 LOSO units) hash-checked; every fold/site summary and the
statistics re-derivation reproduce.

## Purpose

The [structural + functional late-fusion round](structural_functional_fusion.md) reported
paired ΔAUC with a "positive-repeat count / 5" descriptor. A reviewer would ask two things:
(1) is "no increment" distinguishable from "underpowered", i.e. where is the confidence
interval; (2) does the conclusion hold under strict leave-one-site-out (LOSO), not just
mixed-site CV. v2 answers both with a pre-registered equivalence test (TOST, margin
±0.02 AUC), a Nadeau–Bengio corrected interval for the CV deltas, and a full LOSO re-run.
Same frozen QC lock / features / covariances / 5×3 splits as `20260909`. The primary
contrast was made **symmetric** — `full_fusion_structural_mlp` − `full_functional_mlp`
(both add an MLP-derived modality) — and the MLP seed was made repeat-dependent.

## Primary hypothesis not confirmed; QC sensitivity requires a narrower interpretation

**Interpretation updated 2026-09-11 after a post hoc audit.** The frozen protocol, numerical results and original machine-readable decision remain unchanged. See [the statistical audit](paper/STATISTICAL_INTERPRETATION.md) and [aggregate sensitivity results](../results/paper_readiness_20260911/).

| Framework | ΔAUC | Original 90% interval | Supported interpretation |
|---|---:|---|---|
| Mixed-site CV (Nadeau–Bengio, df = 14) | −0.011 | [−0.040, +0.017] | Equivalence to ±0.02 not established |
| Strict LOSO (pair-weighted, site-stratified subject bootstrap) | +0.028 | [+0.009, +0.046] | Positive conditional contrast; a benefit larger than 0.02 is not established |

The protocol required equivalence under both frameworks. That criterion was not met, and the original decision explicitly triggered an audit. The original `B2_meaningful_increment` program label means a meaningful benefit could not be excluded; it is not evidence that the benefit exceeds 0.02. Keep the original endpoint result visible rather than treating a conflicting result as automatically invalid.

| Prespecified QC cohort | LOSO pair-weighted ΔAUC, primary contrast |
|---|---:|
| `primary` (n = 350) | +0.028 [+0.009, +0.046] |
| `warning_free` (n = 302) | −0.086 [−0.161, −0.010] |
| `include_holds` (n = 375) | −0.043 [−0.074, −0.011] |

The signs are sensitive to QC cohort. This does not by itself prove a small-sample artifact, rule out leakage, or establish that LOSO is categorically uninformative. CV and LOSO answer different generalization questions; the later change in narrative emphasis is post hoc.

The earlier report confused NYU's subject fraction with its pair weight: NYU is 139/350 = 39.7% of the primary sample, but contributes 4,774/7,118 = **67.07% of case-control pairs**. The underlying published pair counts and numeric summaries were correct.

Matched-subject decomposition now separates evaluation composition, site weights and changes in the fitted pipelines. For primary → warning_free, the native ΔAUC shift is −0.11319. Its components are −0.11889 from changed pipelines evaluated on the same 302 subjects, +0.00379 from evaluation composition, and +0.00191 from site weights. Thus the earlier claim that the reversal was driven only by which test subjects were included is unsupported.

A further symmetric post hoc decomposition of the common-subject term assigns +0.00398 to changed base/structural predictions and −0.12287 to the final validation-selected fusion weight. NYU's structural weight changes from 0 to 1. These are descriptive allocations including nonlinear interaction, not causal estimates or evidence of an independently replicated biological mechanism.

LOSO uncertainty here conditions on fixed sites and fitted models. It does not capture sampling new sites or retraining uncertainty. The tiny sites contribute little to a pair-weighted summary but can strongly affect a macro summary; report the estimand and weighting explicitly.

## Mixed-site CV — results of the planned reanalysis

| Cohort | Contrast | ΔAUC | 90% CI (df 14) | 90% CI (df 2, conservative) |
|---|---|---:|---|---|
| primary | **P** fusion(structural MLP) − functional MLP | −0.011 | [−0.040, +0.017] | [−0.059, +0.036] |
| primary | S1 functional MLP − confound baseline | −0.007 | [−0.041, +0.027] | [−0.063, +0.050] |
| primary | S2 fusion(structural LR) − functional MLP | −0.011 | [−0.051, +0.029] | [−0.078, +0.055] |
| primary | S3 fusion LR − functional LR | −0.007 | [−0.043, +0.028] | [−0.066, +0.051] |
| primary | S4 image-only: + structural on functional | +0.020 | [−0.018, +0.058] | [−0.043, +0.083] |
| primary | S5 fusion(TIV) − functional(TIV) | −0.008 | [−0.038, +0.022] | [−0.058, +0.042] |
| primary | E1 structural MLP − structural LR | +0.008 | [−0.033, +0.049] | [−0.060, +0.076] |

- **Every confound-plus-imaging contrast (P, S1, S2, S3, S5) has a negative point estimate**
  in all three cohorts. Report each interval rather than using the shared sign as evidence of equivalence.
- **No contrast establishes formal equivalence.** The Nadeau–Bengio correction — which
  accounts for the training-set overlap across the 15 folds — widens every 90% interval
  past −0.02 at n = 350. So the honest CV statement is *no stable positive increment established across analyses;
  equivalence to within ±0.02 remains unconfirmed*. The `20260909` "0 of 5 repeats positive"
  descriptor overstated the certainty.
- The one positive point estimate, **S4**, is the image-only "add structural to functional"
  contrast (+0.020, 11/15 folds positive) — the same effect as `20260909` (+0.017). Under
  LOSO it is +0.012 in `primary` but −0.009 / −0.004 in the other cohorts: not robust.
- `include_holds` P is closest to equivalence at [−0.022, +0.017].

Full tables: [`results/v2_cv_contrast_stats.csv`](../results/v2_cv_contrast_stats.csv),
[`results/v2_loso_contrast_stats.csv`](../results/v2_loso_contrast_stats.csv).
Figure [`v2_F2_cv_bars.png`](../figures/v2_F2_cv_bars.png).

## Calibration

Pooled CV test-fold predictions, per cohort. Calibration is descriptive and does not establish clinical risk validity:

| Model (primary cohort) | ECE | Brier skill score vs prevalence |
|---|---:|---:|
| full_covariates_lr | 0.065 | +0.091 |
| full_functional_mlp | 0.058 | +0.088 |
| full_fusion_structural_mlp | 0.066 | +0.067 |
| image_fusion_mlp | 0.121 | **−0.049** (worse than predicting the base rate) |

`image_fusion_mlp` has a negative Brier skill score in `primary` and `warning_free`.
Pre-registered statement stands: outputs are class-weighted and uncalibrated and must not be
read as individual diagnostic risk. Table:
[`results/v2_calibration_summary.csv`](../results/v2_calibration_summary.csv); figure
[`v2_F3_reliability.png`](../figures/v2_F3_reliability.png).

## What v2 changes about the project conclusion

The original primary equivalence hypothesis was not confirmed. Negative CV point estimates do not establish absence of useful imaging information, and the positive primary LOSO result should remain visible alongside its QC sensitivity. The most defensible conclusion concerns instability of the specified fitted pipelines on reused ADHD-200 cohorts.

The original CV df=2 sensitivity extends to +0.036. An additional post hoc sensitivity using actual model-fit rows in the NB ratio gives a primary df=14 interval about [−0.043,+0.020]. Neither establishes equivalence. These estimator sensitivities should accompany any assertion about excluding a positive increment.

Three overlapping QC cohorts are not independent replications. No clinical, external-validation, or causal claim follows from these analyses.

## Files

- `docs/analysis_v2_protocol.md`, `docs/analysis_v2_deviations.md`
- `results/v2_cv_contrast_stats.csv`, `results/v2_loso_contrast_stats.csv`,
  `results/v2_loso_per_site_deltas.csv`, `results/v2_calibration_summary.csv`
- `figures/v2_F1_loso_forest.png`, `figures/v2_F2_cv_bars.png`, `figures/v2_F3_reliability.png`
- `notebooks/run_structural_fusion_v2.py`, `notebooks/analyze_v2_stats.py`,
  `notebooks/calibration_v2.py`, `notebooks/verify_v2.py`, `notebooks/figures_v2.py`
- Full run outputs (per-fold predictions, `protocol_v2.json`, `verification.json`) are kept
  with the run directory and not committed, consistent with the rest of `results/`.
