# One-page case: measuring what fMRI adds

**Ningyu Sun · Python / PyTorch / scikit-learn / nilearn · ADHD-200**

I built and audited a multi-site fMRI machine-learning workflow to ask two separate questions: does the representation improve image-only prediction, and does imaging add information beyond non-imaging controls?

## Problem and approach

Small, heterogeneous neuroimaging datasets can produce scores that reflect site, motion or demographics. I audited subject identity and labels, used 378 eligible participants, and compared Pearson versus tangent connectivity with logistic regression and a small PyTorch MLP. Five repeated three-fold partitions kept each participant in one role per fold; feature selection, scaling and the tangent reference were fitted using training participants only. Hyperparameters, early stopping and fusion weights used validation data.

## Results and decision

| Comparison | Mean AUC / change |
|---|---:|
| Pearson MLP → tangent MLP | 0.6096 → 0.6453 |
| Paired representation improvement | +0.0357; positive in 5/5 repeats |
| Fuller non-imaging control → control + image predictions | 0.7077 → 0.7127 |
| Paired incremental imaging gain | +0.0050; positive in 4/5 repeats |

The representation improved image-only prediction, while the incremental gain over the fuller control was small and varied with the partition. I retained all repeats and froze the experiment instead of optimizing against the reused test results. These are internal development estimates; they do not establish external validity, causal mechanisms, or clinically useful risk prediction.

## What I can demonstrate

- A traceable path from aggregate findings to cohort version, split protocol, source hashes and model outputs.
- Independent replay of 35,910 frozen test predictions and 60 validation-selected fusion weights, with AUC agreement at floating-point precision.
- A portable package with a runnable synthetic LR/MLP example, checkpoint replay, environment checks and tests for data/role leakage and training-only preprocessing.
- A compact DL implementation: 1,000 selected features → 64 → 16 → 1; **65,121 parameters**; regularization, early stopping and three-seed averaging, with saved learning curves.

For medical AI roles, the case demonstrates neuroimaging QC, explicit covariate controls and careful generalization claims. For general DS/MLE roles, it demonstrates data contracts, reproducible evaluation, numerical debugging, testable pipelines and resource-aware model decisions.

## Boundaries and ownership

I led the project with AI-assisted implementation and review. This release replays frozen outputs, exercises real split preparation, and runs a synthetic training demonstration; it does not claim a fresh full 15-fold training run or raw-image reconstruction. Historical 409-person and structural experiments are versioned separately.

[Code and quickstart](README.md) · [Evidence](results/fmri_378/verification.json) · [Technical deck](docs/portfolio/ADHD_fMRI_technical_portfolio.pptx) · [Demo](docs/portfolio/DEMO.md)
