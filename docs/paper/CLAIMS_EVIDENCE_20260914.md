# Claims, evidence and limits — 2026-09-14

Scope: retrospective ADHD-200 structural/fMRI incremental-value study. Proposed manuscript framing: reproducible but QC- and evaluation-dependent structural incremental value. This is a review draft, not a scientific release.

| Defensible statement | Evidence | Boundary / wording to avoid |
|---|---|---|
| VERIFIED: fresh feature-level computation reproduced 66/66 units | fresh_refit/run/verified_reproduction.json; 45 CV + 21 LOSO, 17 outputs/unit, validation/test maximum difference 0 | Frozen derivatives were inputs. Raw MRI preprocessing and independent algorithm reimplementation are not established. Shared implementation errors can reproduce. |
| VERIFIED: original statistical decision reproduced | fresh_refit/statistics/recomputation_verification.json; five tables, decision agreement | Reproducing a decision does not validate its assumptions. Historical REPORT_stats.md prose is not the current interpretation. |
| Primary CV structural increment remains inconclusive | STATISTICAL_INTERPRETATION.md; ΔAUC −0.01139, 90% CI [−0.04003, +0.01725] | Neither a reliable positive increment nor equivalence within ±0.02 is established. A non-significant result is not proof of no value. |
| LOSO estimate depends on cohort and aggregation | SENSITIVITY_RESULTS.md; pair-weighted primary +0.02754, warning-free −0.08565, include-holds −0.04292 | Cohorts overlap; these are sensitivity analyses, not independent replications. Primary lower 90% bound +0.00947 does not establish increment >0.02. |
| Equal-site and pair-weighted answers differ | loso_summaries.csv; primary macro Δ −0.01543 | Explicitly define estimand. NYU has 67.07% of case-control pair weight, but primary NYU increment is zero. Do not attribute the primary positive increment to NYU. |
| Final fusion selection is a sensitivity contributor | fusion_decomposition_summary.csv; primary→warning-free pipeline −0.118894, prediction component +0.003978, final-alpha component −0.122872 | Post-hoc descriptive decomposition, not causal identification. Validation bootstrap conditions on fixed fitted models. |
| Generalisation and clinical utility remain unestablished | protocol/deviations; site and QC sensitivity | No independent external cohort or expert full-volume anatomical QC has been verified. Avoid diagnostic-readiness claims. |

Main contrast is full_fusion_structural_mlp minus full_functional_mlp. The baseline includes age, sex, site and motion. TIV is imaging-derived. The actual LOSO inner selection used one stratified 85/15 split rather than the planned three-fold inner procedure, and did not refit on all six training sites after selection; see METHODS_CLARIFICATION_20260914.md. Data had been explored before v2; a frozen protocol hash is not prospective registration.

YELLOW — understanding not yet assessed: be able to explain equivalence versus uncertainty, pair weighting versus equal-site weighting, validation-only tuning, and conditional versus full-pipeline uncertainty.
