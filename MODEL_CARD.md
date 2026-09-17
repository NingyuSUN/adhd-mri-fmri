# Model Card: ADHD-200 MRI/fMRI Research Benchmark

## Summary

This repository contains research models for ADHD-versus-control classification from structural MRI and resting-state fMRI. No model is released as a clinical predictor. The strongest observed cross-site performance comes from demographic and motion/QC variables, not neuroimaging features.

## Intended use

- research benchmarking
- teaching confound-aware neuroimaging evaluation
- reproduction of strict subject/site split experiments
- development of improved harmonization or phenotyping methods

## Out-of-scope use

- clinical diagnosis or screening
- treatment selection
- individual risk scores
- use on children or sites outside the documented research context without external validation

## Data

ADHD-200 multi-site structural MRI, resting-state fMRI derivatives, phenotypic labels, demographics, and motion/QC variables. Raw data are not distributed by this repository.

## Historical n=409 benchmark evaluation

Two evaluation frameworks were used on the locked `n=409` fMRI cohort:

- **Portfolio benchmark (primary presentation metric):** repeated four-fold
  cross-validation stratified jointly by site and diagnosis (5 repeats, 20
  outer evaluations); imputation, scaling, and hyperparameter selection are
  refit inside every training fold.
- **Strict nested leave-one-site-out (robustness stress test):** split unit is
  subject/site; primary metric is macro AUC across evaluable held-out sites;
  preprocessing and hyperparameter selection use training sites only.

Every image model is required to be compared against a confound-only baseline
under the same framework.

## Performance

Repeated site+label-stratified CV (`n=409`, mean AUC ± SD):

- age + sex + motion/QC: 0.677 ± 0.058
- motion/QC: 0.641 ± 0.057
- confounds + BrainLM: 0.619 ± 0.040
- FC + BrainLM: 0.595 ± 0.031
- FC ROI summary: 0.583 ± 0.036
- spectral: 0.570 ± 0.035
- frozen BrainLM: 0.529 ± 0.043

Strict nested LOSO, macro AUC:

- age + sex + motion/QC: 0.686
- motion/QC: 0.664
- age + sex: 0.583
- frozen BrainLM: 0.512
- FC + BrainLM: 0.501
- spectral: 0.492
- FC ROI summary: 0.477

Structural MRI, strict LOSO OOF AUC: age + sex 0.619 vs. pretrained Swin-T
0.579 vs. ROI-guided CNN 0.470 — the non-imaging baseline outperforms every
tested structural model under site-held-out evaluation.

The tested image representations do not provide stable incremental value beyond
confounds in either framework. Full model-by-model tables:
[RESULTS.md](RESULTS.md).

## Limitations and risks

- multi-site prevalence, scanner, and acquisition differences
- diagnostic and phenotypic heterogeneity
- motion correlated with diagnosis and image quality
- modest sample size relative to model capacity
- incomplete external validation
- instability of site-wise estimates at small sites
- risk that pooled metrics overstate performance

## Release decision

No deployable trained model is released. Research code and aggregate results are provided to document the benchmark and its negative/boundary conclusion.

## Later multimodal v2 analysis

The three QC cohorts (350/302/375) use paired multimodal comparisons under repeated CV and site-held-out evaluation. The primary equivalence criterion was not met. Interpretations are updated in [the statistical audit](docs/paper/STATISTICAL_INTERPRETATION.md); the earlier n=409 metrics above should not be treated as paired baselines for this later cohort.
