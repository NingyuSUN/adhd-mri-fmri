# Statistical interpretation audit (2026-09-11)

This audit is post hoc and preserves the frozen v2 protocol and original decision.json. It supersedes overstrong narrative interpretations, not the historical records. The publication should separate planned analysis, protocol deviations and these later sensitivity analyses.

## What the pre-specified primary analyses establish
The primary comparison remains structural-MLP fusion minus functional-MLP fusion on the primary cohort, conditional on the non-imaging variables used. The protocol required equivalence in BOTH CV and LOSO. Neither original result satisfies that requirement. The primary hypothesis was not confirmed.

Original corrected CV: delta -0.01139, 90% interval [-0.04003,+0.01725] with df=14. This interval fails two-sided equivalence to +/-0.02. Its upper limit is below +0.02 under this particular approximate estimator, but that exclusion does not hold under the pre-specified df=2 sensitivity (upper +0.03609). Report both, do not generalize one estimator's bound to all tested settings.

Original LOSO: delta +0.02754, 90% interval [+0.00947,+0.04626]. The interval supports a positive conditional contrast at the corresponding one-sided level. It does NOT establish an increment larger than +0.02 because the lower limit is below +0.02. The historical B2 label meaningful_increment must be accompanied by this distinction. A 90% interval excluding zero is not automatically a two-sided 5% test.

## Do not discard a conflicting endpoint
The original machine-readable decision retained FALSIFICATION TRIGGERED / audit-before-interpreting. Keep that fact. The failure of equivalence and disagreement across QC cohorts are results. They do not establish that the positive LOSO estimate is an artifact, that LOSO is invalid, or that ADHD-200 categorically cannot detect small effects. Mixed-site CV and LOSO target different generalization settings; changing endpoint emphasis after seeing results must be disclosed.

Sign reversal cannot rule out leakage. An absence-of-leakage claim requires a direct data-flow and split audit. Training-only transformations and identity checks are useful engineering evidence, but cannot identify all shared conceptual errors or adaptive reuse of data.

## Correction to the reported NYU weight
NYU has 139/350 = 39.7% of primary-cohort subjects, but 77*62 = 4,774 of 7,118 within-site case-control pairs, so its primary pair-weight is 67.07%, not ~40%. The earlier narrative confused participant fraction with AUC pair-weight. The published per-site pair counts and aggregate numeric estimate were correct; this is a reporting correction.

## Uncertainty and protocol issues
- Original LOSO resampling fixes the seven sites and trained models. It does not capture variability of training, hyperparameter selection or sampling new sites. The added bootstrap fixes site and class counts and primary site weights where specified, so its target differs from the original bootstrap; it is labeled as such.
- The original NB correction used test/(outer training plus validation)=0.5. The actual estimator fits model parameters on approximately 53% of all subjects, retaining approximately 13% for inner validation. An additional disclosed sensitivity uses the mean actual test/fit ratio (~0.626). The primary df=14 interval becomes approximately [-0.04307,+0.02028]. This is a sensitivity to the correction convention, not a claim that one alternative is a uniquely valid estimator for the adaptive fitted pipeline.
- The written B2 and B4 conditions are not literally disjoint: e.g. [+0.009,+0.046] meets B2 and the second B4 expression. The executed ordered if/else assigns B2. Future decision tables should separate interval-sign, materiality and equivalence indicators; the original program/decision remain unchanged.
- A statement that multiplicity is harmless because observed effects are negative is not a valid general error-control justification. Keep the pre-specified primary contrast distinguished; label the remaining comparisons exploratory/sensitivity and disclose lack of family-wise adjustment.
- The LOSO inner split was a single stratified 85/15 holdout rather than the written inner 3-fold/refit plan. This is disclosed in the existing deviations record. It can contribute model-selection variability; outer test separation alone does not quantify its effect.
- Frozen plans and hashes are not proof of an externally timestamped prospective registration. The data and earlier model results had already been examined. Describe v2 as a planned reanalysis of previously used data and document the actual timeline.
- Three overlapping QC cohorts are not three independent replications. Repeated CV predictions of one participant must not be counted as independent participants. Pooled calibration curves are descriptive; n counts predictions, not unique people.

## QC/LOSO decomposition estimand
Let d_A and d_B be the primary contrast under models trained in cohorts A and B. For each site, compute both on the same intersecting held-out subjects and on their respective full evaluation sets. At the fixed primary-cohort site weights, define:

- model contribution = d_B(common) - d_A(common)
- evaluation-composition contribution = [d_B(full)-d_B(common)] - [d_A(full)-d_A(common)]
- site-weight contribution = [d_B(native weights)-d_B(fixed weights)] - [d_A(native weights)-d_A(fixed weights)]

These three terms exactly reconstruct the native summary difference. They are descriptive contributions. The model contribution bundles changes in training composition, tuning, selected fusion weights, optimization and initialization; it does not isolate one of those causes. Removing a site's contribution from a summary is not equivalent to retraining without that site. The current analysis uses no new test-driven model selection.

## Publication wording
On these reused ADHD-200 cohorts and the specified pipelines, the original primary equivalence hypothesis was not confirmed. Mixed-site CV gave a small negative point estimate with uncertainty crossing the equivalence boundary. The primary LOSO estimate was positive, but its direction changed across pre-specified QC cohorts. Subsequent matched-subject analyses show that these changes persist when evaluation subjects and site weights are held fixed, implicating changes in the trained pipelines rather than merely the composition of the test sample. The analyses do not establish a stable incremental benefit, clinical utility, absence of neurobiological signal, or a general failure of LOSO.

## References and evidence
- Original protocol: ../analysis_v2_protocol.md; deviations: ../analysis_v2_deviations.md; historical results: ../analysis_v2_results.md.
- Brown et al. (2012), ADHD-200 Global Competition: diagnosing ADHD using personal characteristic data can outperform resting state fMRI measurements. https://pmc.ncbi.nlm.nih.gov/articles/PMC3460316/
- Varoquaux (2018), Cross-validation failure: Small sample sizes lead to large error bars. https://doi.org/10.1016/j.neuroimage.2017.06.061
- Rosenblatt et al. (2024), Data leakage inflates prediction performance in connectome-based machine learning models. https://doi.org/10.1038/s41467-024-46150-w
- Collins et al. (2024), TRIPOD+AI reporting guidance. https://doi.org/10.1136/bmj-2023-078378

No external validation or human anatomical re-review was performed by this audit. Professional statistical and neuroimaging review remains necessary before publication.

## Follow-up after the initial decomposition
A second, explicitly post hoc decomposition cross-applies the two cohorts' validation-selected final structural fusion weights to their fixed predictions on common held-out subjects. Symmetric averaging over the two application orders splits the nonlinear interaction equally. This describes a model-prediction contribution and a final-alpha contribution; it is not a causal attribution. For primary versus warning_free, the common-model shift -0.118894 decomposes into prediction contribution +0.003978 and final-alpha contribution -0.122872. NYU's final structural alpha changes from 0 to 1.

A separate validation-only site-by-label bootstrap examines this final selector for all 66 units. Fitted models, earlier regularization/early stopping and upstream functional-fusion selection are fixed. Its displayed test-delta quantiles are conditional selector-sensitivity summaries, not confidence intervals for the full training procedure. No test scores select a weight or preferred cohort.
