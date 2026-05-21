# Results Summary

This file summarizes the current experimental status. Replace placeholder values with final saved result tables after rerunning the standardized scripts.

## Structural MRI: Single-slice Baseline

Current interpretation:

- The single-slice T1 CNN is useful as a sanity-check baseline.
- Validation AUC is often near chance level.
- Accuracy can be misleading because the model may predict mostly control subjects.
- Threshold analysis shows that weak ranking performance does not necessarily translate into clinically meaningful recall.

Recommended table:

| Experiment | Split | Unit | AUC | Recall@0.5 | Precision@0.5 | Notes |
|---|---|---|---:|---:|---:|---|
| T1 single-slice CNN | subject-level | subject | TBD | TBD | TBD | sanity-check baseline |

## Structural MRI: Multi-slice Baseline

Current interpretation:

- Multi-slice extraction slightly increases information per subject.
- Subject-level aggregation is required.
- Performance remains weak or close to chance in strict subject-level evaluation.

Recommended table:

| Experiment | K slices | Split | Aggregation | Subject AUC | Notes |
|---|---:|---|---|---:|---|
| T1 multi-slice CNN | 5 | subject-level | mean | TBD | no leakage |

## Structural MRI: ROI-guided CNN

Current interpretation:

- ROI-guided slice selection tests a fronto-striatal/cingulate hypothesis.
- MNI152 2mm rigid registration and Harvard-Oxford atlas make slice selection anatomically comparable across subjects.
- Bootstrap CI should be reported because sample size can be small and site-specific.

Recommended table:

| Experiment | Registration | ROI | Normalization | Aggregation | Subject AUC | 95% CI |
|---|---|---|---|---|---:|---|
| ROI-guided CNN | Rigid MNI152 2mm | Harvard-Oxford | z-score | mean | TBD | TBD |

## Ablation and Site Bias

Current interpretation:

- Ablation is used to test mechanisms, not only to chase higher AUC.
- Site-only and site+age+sex baselines are necessary because multi-site ADHD data can contain strong site-label association.
- If no-normalization improves AUC, this should be treated as a warning sign rather than a straightforward improvement.

Recommended table:

| Model | Features/Input | OOF AUC | Interpretation |
|---|---|---:|---|
| Site-only baseline | site | TBD | estimates site-label shortcut |
| Age+sex baseline | age, sex | TBD | demographic confound baseline |
| Site+age+sex baseline | site, age, sex | TBD | combined non-image baseline |
| Full MRI model | image | TBD | must exceed confound baselines |
| No-normalization ablation | image | TBD | high AUC may indicate scanner shortcut |
| Random-slice ablation | image | TBD | tests ROI specificity |

## fMRI Connectivity GNN

Current interpretation:

- Early fMRI experiments show that graph construction is the key bottleneck.
- Requiring identical graph dimensions without careful ROI handling can reduce usable NYU graphs from a much larger labeled set to a very small subset.
- The improved direction is fixed ROI node definition with zero-padding or finite-value replacement when needed.

Recommended table:

| Experiment | Site(s) | ROI atlas | Graph construction | N graphs | AUC | Notes |
|---|---|---|---|---:|---:|---|
| fMRI GCN prototype | NYU | Harvard-Oxford cortical | fixed ROI graph | TBD | TBD | prototype |

## What Should Be Reported Before Claiming a Positive Result

Minimum recommended reporting package:

1. Subject-level AUC.
2. 95% bootstrap confidence interval.
3. Fold-wise AUC.
4. Site-wise performance.
5. Site-only and site+age+sex baselines.
6. Ablation table.
7. Leave-one-site-out evaluation.
8. Clear statement that the model is not a clinical diagnostic system.
