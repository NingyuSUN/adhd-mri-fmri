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

## Headline: ADHD-200 cannot support strict LOSO for a small AUC effect

The pre-registered decision rule compares the primary contrast under both frameworks:

| Framework | ΔAUC | 90% interval | Pre-registered branch |
|---|---:|---|---|
| Mixed-site CV (Nadeau–Bengio, df = 14) | −0.011 | [−0.040, +0.017] | inconclusive / underpowered |
| Strict LOSO (pair-weighted, site-stratified subject bootstrap) | +0.028 | [+0.009, +0.046] | **meaningful increment** |

The two frameworks disagree, which the protocol flags for audit. **The audit shows the LOSO
result is a small-sample artifact of the ADHD-200 site structure, not a real effect:**

| Prespecified QC cohort (overlap > 85% of subjects) | LOSO pair-weighted ΔAUC, primary contrast |
|---|---:|
| `primary` (n = 350) | **+0.028** [+0.009, +0.046] |
| `warning_free` (n = 302) | **−0.086** [−0.161, −0.010] |
| `include_holds` (n = 375) | **−0.043** [−0.074, −0.011] |

Three cohorts differing by at most 48 subjects swing the estimate by 0.11 AUC and flip the
pre-registered branch from "increment" to "decrement". The mechanism is visible in
[`figures/v2_F1_loso_forest.png`](../figures/v2_F1_loso_forest.png) and
[`results/v2_loso_per_site_deltas.csv`](../results/v2_loso_per_site_deltas.csv):

- **NYU** carries ~40% of the pair weight. Its held-out ΔAUC for the *same* contrast is
  0.000 in `primary`, −0.145 in `warning_free`, −0.051 in `include_holds` — a ±0.15 AUC
  swing on the same held-out site, driven only by which subjects the QC cohort includes.
  The LOSO summary sign follows NYU.
- The two smallest held-out sites, **Peking_2** (n = 14) and **Peking_3** (n = 6), have
  95% within-site bootstrap intervals spanning roughly ±0.5 to ±1.0 — no information.
- In `primary`, the +0.028 is carried by two mid-size sites (KKI +0.11, OHSU +0.15) whose
  held-out AUC on a 32–82-subject test set is itself a high-variance quantity.

There is no leakage path — the held-out site never touches any fit, and inner
hyperparameter selection is confined to the six training sites; a leak would help all three
cohorts, not flip the sign. **With 7 acquisition sites (one dominant, two below n = 15),
strict LOSO in ADHD-200 cannot adjudicate a ΔAUC on the order of 0.01–0.02. The held-out
summary is hostage to the subject composition of the largest site.** This is why the
repository uses **repeated site-and-label-stratified subject-level CV as the primary
endpoint** and treats LOSO as a qualitative domain-shift stress test only.

## Mixed-site CV — the confirmatory result

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
  and an upper bound ≤ +0.03, in all three cohorts. The point-estimate picture matches
  `20260909` exactly.
- **No contrast establishes formal equivalence.** The Nadeau–Bengio correction — which
  accounts for the training-set overlap across the 15 folds — widens every 90% interval
  past −0.02 at n = 350. So the honest CV statement is *no meaningful positive increment;
  equivalence to within ±0.02 is underpowered*. The `20260909` "0 of 5 repeats positive"
  descriptor overstated the certainty.
- The one positive point estimate, **S4**, is the image-only "add structural to functional"
  contrast (+0.020, 11/15 folds positive) — the same effect as `20260909` (+0.017). Under
  LOSO it is +0.012 in `primary` but −0.009 / −0.004 in the other cohorts: not robust.
- `include_holds` P is closest to equivalence at [−0.022, +0.017].

Full tables: [`results/v2_cv_contrast_stats.csv`](../results/v2_cv_contrast_stats.csv),
[`results/v2_loso_contrast_stats.csv`](../results/v2_loso_contrast_stats.csv).
Figure [`v2_F2_cv_bars.png`](../figures/v2_F2_cv_bars.png).

## Calibration

Pooled CV test-fold predictions, per cohort. All four report models are poorly calibrated:

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

## What v2 changes about the project's conclusion

Nothing in the direction of the conclusion — it sharpens the wording and adds the LOSO
justification:

1. Mixed-site CV point estimates continue to show that adding functional or structural MRI
   to age + sex + site + motion does not raise AUC. But at n = 350 the corrected intervals
   cannot *prove* equivalence to ±0.02 — the responsible phrasing is "no meaningful positive
   increment, equivalence underpowered", not "structural MRI adds nothing".
2. Strict LOSO cannot contribute evidence for or against the hypothesis at this sample size;
   its estimate is dominated by the subject composition of the largest held-out site. This
   is a documented result, and it is the reason LOSO is a stress test rather than the
   primary endpoint in this repository.

## Files

- `docs/analysis_v2_protocol.md`, `docs/analysis_v2_deviations.md`
- `results/v2_cv_contrast_stats.csv`, `results/v2_loso_contrast_stats.csv`,
  `results/v2_loso_per_site_deltas.csv`, `results/v2_calibration_summary.csv`
- `figures/v2_F1_loso_forest.png`, `figures/v2_F2_cv_bars.png`, `figures/v2_F3_reliability.png`
- `notebooks/run_structural_fusion_v2.py`, `notebooks/analyze_v2_stats.py`,
  `notebooks/calibration_v2.py`, `notebooks/verify_v2.py`, `notebooks/figures_v2.py`
- Full run outputs (per-fold predictions, `protocol_v2.json`, `verification.json`) are kept
  with the run directory and not committed, consistent with the rest of `results/`.
