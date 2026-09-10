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

## Evaluation

- primary design: strict nested leave-one-site-out validation
- split unit: subject/site
- primary metric: macro AUC across evaluable held-out sites
- preprocessing and hyperparameter selection: training sites only
- required comparison: confound-only baseline

## Performance

On the locked fMRI cohort (`n=409`):

- age + sex + motion/QC: macro AUC 0.686
- motion/QC: 0.664
- age + sex: 0.583
- frozen BrainLM: 0.512
- FC + BrainLM: 0.501
- spectral: 0.492
- FC ROI summary: 0.477

The tested image representations do not provide stable incremental value beyond confounds.

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
