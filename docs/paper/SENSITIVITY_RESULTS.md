# Post hoc sensitivity results — 2026-09-11

The main contrast is structural-MLP fusion minus confound-plus-functional fusion. All results below use already saved held-out predictions; no new weights or models are selected on a test set. These analyses were designed after the original results were known and do not constitute independent confirmation.

## Exact QC decomposition

All three components add to the total native pair-weighted shift. Fixed weights are the primary cohort's site-wise positive-negative pair counts. Model comparisons use the same intersecting held-out people at each site.

| Cohort transition | Shared people | Total ΔAUC shift | Common-subject fitted-pipeline contribution | Evaluation-composition contribution | Site-weight contribution |
|---|---:|---:|---:|---:|---:|
| Primary → No warnings | 302 | −0.113186 | −0.118894 | +0.003795 | +0.001913 |
| Primary → Include holds | 350 | −0.070457 | −0.065327 | −0.003533 | −0.001596 |
| No warnings → Include holds | 302 | +0.042729 | +0.057892 | −0.011653 | −0.003510 |

The algebraic reconstruction residual is zero to floating-point precision. Evaluation composition and aggregation weights alone do not explain the main reversal. The fitted-pipeline contribution initially bundles altered training composition, tuning, fusion selection and optimization; it is not a causal attribution.

## Final fusion weight versus base predictions

The final candidate score is `(1-alpha) * functional_score + alpha * structural_score`. Both cohorts' originally selected alphas can be cross-applied to both cohorts' fixed predictions on the common test subjects. Averaging the two attribution orders shares the nonlinear interaction symmetrically.

| Cohort transition | Common-subject pipeline shift | Prediction contribution | Final-alpha contribution |
|---|---:|---:|---:|
| Primary → No warnings | −0.118894 | +0.003978 | −0.122872 |
| Primary → Include holds | −0.065327 | −0.021565 | −0.043762 |
| No warnings → Include holds | +0.057892 | −0.021412 | +0.079305 |

The contribution from validation-selected final alpha dominates the primary→no-warnings difference under this descriptive decomposition. It is not proof that changing alpha alone in a prospective experiment would reproduce the same effect. Earlier functional-fusion weight selection remains bundled into the prediction component.

## NYU weighting and selector sensitivity

NYU contains 139/350 = 39.7% of primary participants but contributes 4,774/7,118 = 67.07% of within-site case-control pairs. The earlier report's 40% pair-weight was a prose error; its published pair counts were correct.

| QC cohort | NYU final structural alpha | Inner validation n | Probability of reselecting original alpha | Probability of alpha=0 |
|---|---:|---:|---:|---:|
| Primary | 0 | 32 | 92.0% | 92.0% |
| No warnings | 1 | 29 | 50.9% | 20.1% |
| Include holds | 0.25 | 33 | 33.7% | 42.2% |

These probabilities come from 1,000 site-by-label bootstrap samples of each fixed inner validation set. Fitted models, regularization, early stopping and earlier fusion selection are fixed. This quantifies uncertainty of the final selector conditional on those choices; it does not estimate all uncertainty from repeating training or recruiting new sites. Test-delta quantiles in the CSV are descriptive selector-sensitivity summaries, not full-procedure confidence intervals. All 66 units were analyzed, not only NYU.

## Interval sensitivity

The original primary CV mean ΔAUC is −0.011391. Its corrected 90% interval is [−0.040031,+0.017249] with the original outer-training ratio and df=14, versus [−0.058871,+0.036090] with df=2. An additional actual-fit-row ratio sensitivity gives [−0.043066,+0.020284] with df=14. These are estimator-specification sensitivities, not repeated independent studies. None establishes two-sided equivalence to ±0.02.

The added LOSO bootstrap fixes sites, class counts and trained predictions. Original site-only resampling and new site-by-label resampling have different conditional targets; both are retained and labeled. Neither samples new training datasets or new acquisition sites.

## Reproduction evidence completed for these analyses

- Original 42-row CV contrast table, 84-row LOSO contrast table, 147-row site table, 120-row calibration bins and 12-row calibration summary re-executed in a clean environment: all numeric differences zero.
- Original `decision.json` reproduced exactly, including its audit trigger.
- Original three figures regenerated from those tables.
- New aggregate tables and four publication figures are linked below. Fresh 66-unit training is a separate execution with a separate [completion report](FRESH_REPRODUCTION_STATUS.md); the statistical verification above must not be described as fresh model training.

## Artifacts

- [Aggregate tables](../../results/paper_readiness_20260911/)
- [QC decomposition figure](../../figures/paper_readiness_20260911/F1_qc_decomposition.png)
- [Site contribution figure](../../figures/paper_readiness_20260911/F2_site_contributions.png)
- [CV interval sensitivity figure](../../figures/paper_readiness_20260911/F3_cv_interval_sensitivity.png)
- [NYU selector stability figure](../../figures/paper_readiness_20260911/F4_NYU_selector_stability.png)
- [Statistical interpretation](STATISTICAL_INTERPRETATION.md)
- [Reproduction instructions](../../reproduction/README.md)
