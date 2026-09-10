# Structural + functional late-fusion (QC-locked paired analysis)

This analysis was run after the frozen fMRI benchmark to answer one question:

> Does subject-level **structural** MRI (regional volume fractions) add stable predictive
> information **beyond functional** connectivity and the non-imaging confound baseline,
> when every model is retrained on the same QC-locked subjects and the same original
> repeat/fold identities?

It is not a search for a higher fMRI score. The frozen fMRI experiments are untouched.

## Design (frozen before training)

- **Cohorts (QC-locked, fixed before any model was run).** Diagnosis-blind sampled QC of 378
  subjects: 302 coarse-review candidates, 48 signal-warning, 25 unresolved anatomical HOLD,
  3 image-quality failures.
  - `primary` = 350 (302 + 48)
  - `warning_free` = 302 (no warnings, no holds)
  - `include_holds` = 375 (378 − 3 failures; keeps the 25 holds)
  - Cohorts are a prespecified sensitivity design, **not** selected by score.
- **Splits.** The exact saved 5-repeat × 3-fold subject-level identities from the parent
  benchmark, filtered by QC cohort membership. No regeneration.
- **Structural features.** 98 automated region volumes / TIV fractions (68 cortical +
  30 subcortical/CSF), **not cortical thickness**. Separate explicit-TIV covariate models.
- **Functional features.** A424 tangent-space connectivity; within-subject Ledoit–Wolf
  covariance; geometric-mean reference point, ANOVA top-1000 selection and scaler all
  fit on the retained training fold only.
- **Models.** L2 logistic regression (C ∈ {0.01, 0.1, 1, 10}, validation-selected, ties → smaller C)
  and a fixed 64/16 GELU MLP (dropout 0.4/0.3, patience 12, max 80 epochs, seeds
  1200/2200/3200 + fold, equal-weight 3-seed ensemble). No architecture grid.
- **Fusion.** Validation-only convex weights α ∈ {0, 0.25, 0.5, 0.75, 1}; ties prefer the
  smaller added-modality weight; sequential covariate + functional, then structural.
- **Metric.** Mean of fold AUC then mean across the 5 repeats; within-site pair-weighted
  AUC secondary; AP / balanced accuracy / Brier descriptive only. **The repeat range is
  not a confidence interval.**

Full frozen spec: `protocol.json` in the release bundle (`qc_sha256`
`e03ad883…8ddc4`).

## Two comparison families — do not conflate

1. **Image-only:** `structural_lr`, `structural_tiv_lr`, `structural_mlp`, `tangent_lr`,
   `tangent_mlp`, `image_fusion_lr`, `image_fusion_mlp`, `tiv_lr`.
2. **With auxiliary information:** anything prefixed `full_covariates_*`, `full_functional_*`,
   `full_fusion_*` — these include age, sex, site and head-motion. Their AUC **cannot** be
   described as image-only performance.

Note on naming: the added modality in `full_fusion_mlp` is `structural_lr` (structural
**logistic-regression** predictions), not `structural_mlp`. Only `full_fusion_structural_mlp`
adds the structural MLP. MLP ensemble seeds do not include the repeat index, so the same
fold number reuses the same three initializations across repeats.

## Results — `primary` cohort (n = 350), mean AUC over 5 repeats

| Model | mean AUC | within-site AUC | min–max repeat |
|---|---:|---:|---:|
| full_covariates_tiv_lr (age+sex+site+motion+TIV, **no imaging**) | 0.712 | 0.673 | 0.700–0.724 |
| full_covariates_lr (non-imaging control) | 0.710 | 0.669 | 0.693–0.720 |
| full_functional_tiv_mlp (control + functional) | 0.709 | 0.666 | 0.697–0.717 |
| full_functional_mlp (control + functional) | 0.698 | 0.652 | 0.669–0.717 |
| full_fusion_tiv_mlp | 0.698 | 0.657 | 0.690–0.714 |
| full_fusion_structural_mlp (control + functional + structural MLP) | 0.690 | 0.644 | 0.667–0.713 |
| full_fusion_mlp (control + functional + structural LR) | 0.687 | 0.645 | 0.669–0.716 |
| image_fusion_mlp (image-only: functional + structural) | 0.638 | 0.606 | 0.617–0.655 |
| image_fusion_lr | 0.632 | 0.598 | 0.613–0.645 |
| structural_mlp | 0.624 | 0.582 | 0.577–0.652 |
| structural_tiv_lr | 0.614 | 0.579 | 0.571–0.636 |
| tangent_mlp | 0.621 | 0.581 | 0.602–0.642 |
| tangent_lr | 0.615 | 0.574 | 0.603–0.635 |
| structural_lr | 0.618 | 0.581 | 0.572–0.644 |
| tiv_lr | 0.501 | 0.504 | 0.442–0.530 |

All 17 models per fold, all 3 cohorts, all 6 metrics: `results/structural_functional_fusion_summary.csv`.

## Paired increments (mean Δ AUC over 5 repeats; positive-repeat count in parentheses)

| Contrast | primary | warning_free | include_holds |
|---|---:|---:|---:|
| full_functional_mlp − full_covariates_lr (does functional add to controls?) | −0.013 (1/5) | −0.005 (2/5) | −0.003 (2/5) |
| full_fusion_mlp − full_functional_mlp (does structural LR add on top?) | −0.010 (0/5) | −0.006 (1/5) | −0.007 (0/5) |
| full_fusion_structural_mlp − full_functional_mlp (does structural MLP add on top?) | −0.008 (0/5) | −0.006 (1/5) | −0.001 (2/5) |
| image_fusion_mlp − tangent_mlp (image-only: does structural add to functional?) | +0.017 (5/5) | +0.007 (3/5) | +0.002 (2/5) |
| structural_mlp − structural_lr | +0.006 (5/5) | +0.011 (4/5) | +0.022 (5/5) |

Full table incl. within-site deltas: `results/structural_functional_fusion_paired_deltas.csv`.

## Interpretation

- The strongest model in every cohort is a **non-imaging** one (age + sex + site + motion,
  ± TIV), at AUC ≈ 0.71.
- Adding functional imaging to that control does not help (negative or flat in all three
  cohorts). Adding structural volume on top of control + functional does not help either
  (negative in all three cohorts, 0–1 of 5 repeats positive).
- The one positive image-derived increment is **within the image-only family**: adding
  structural to the functional model raises AUC by +0.017 in `primary` (5/5 repeats), but
  this shrinks to +0.007 (3/5) and +0.002 (2/5) in the other two QC cohorts, so it is not
  a robust effect. Image-only absolute performance (0.62–0.64) is well below the
  non-imaging control.
- `structural_mlp` consistently edges `structural_lr` (+0.006 to +0.022, 4–5 of 5 repeats),
  i.e. the small structural signal is slightly better captured non-linearly — but it does
  not change the incremental-value conclusion.

This reproduces the repository's overall finding under a stricter design: structural MRI
and functional MRI both fail to provide stable information beyond demographic and
acquisition confounds. Here the structural, functional and fusion models were retrained
together on one frozen protocol, one QC-locked cohort set and the original subject
identities, so subset estimates are not compared against the frozen 378-subject numbers
as if paired.

## Verification

`verification.json` in the release bundle: `status: verified`, 45 folds, 17 models each.
For every fold the release script independently recomputed tangent / structural / covariate
preprocessing and replayed all 17 saved model outputs against the stored validation/test
predictions (`hashes`, `preprocessing`, `roles`, `validation_selection`,
`all17_prediction_replay` all true). The run was executed and verified end-to-end on a
single Linux host for floating-point consistency.

## Limitations (in addition to `../LIMITATIONS.md`)

- Adaptive, repeatedly-used internal cohort; no external validation; no LOSO in this round.
- Validation folds carry multi-stage selection (C, early stopping, α) → optimistic test
  estimates.
- Sampled assistant QC, not expert whole-volume acceptance. The 25 HOLD subjects still
  need specialist review; `primary` excludes them by the prespecified rule.
- Outputs are not calibrated to clinical risk. Not a diagnostic tool.
