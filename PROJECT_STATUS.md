# Project Status

This is an active research repository for ADHD classification using structural MRI and resting-state fMRI.

## Completed Components

| Component | Status | Notes |
|---|---:|---|
| BIDS T1 path collection | Done | Site-wise subject and image discovery implemented |
| Label extraction from `participants.tsv` | Done | Handles text diagnosis labels and encoding issues |
| QC filtering | Done | Uses anatomical QC pass where available |
| Subject-level deduplication | Done | Prevents duplicate T1 runs from creating leakage |
| Single-slice T1 CNN | Done | Baseline for pipeline validation |
| Multi-slice T1 CNN | Done | Uses subject-level split and mean aggregation |
| Leakage demonstration | Done | Shows why slice-level random split is invalid |
| MNI152 2mm rigid registration | Done | ANTsPy-based registration with caching |
| Harvard-Oxford ROI-guided slice selection | Done | Frontal/cingulate/subcortical ROI prior |
| ROI-guided T1 CNN | Done | Slice-level training, subject-level evaluation |
| Ablation experiments | Done | ROI, registration, normalization, aggregation |
| Site-bias baselines | In progress | Site-only and site+age+sex models included |
| fMRI manifest construction | Done | Scans BIDS fMRI and recovers labels where possible |
| fMRI connectivity graph construction | Done | Harvard-Oxford ROI time series and correlation graphs |
| GNN model for fMRI | Prototype | GCN prototype with fixed ROI graph representation |

## Current Interpretation

The structural MRI branch suggests that simple T1 slice-based models produce weak and unstable ADHD discrimination under strict subject-level evaluation. The ablation and site-bias analyses indicate that apparent performance must be interpreted cautiously because site/scanner information can provide non-biological predictive shortcuts.

The fMRI branch is now the more promising direction because ADHD may be better represented as a functional/network-level condition than as a purely structural anatomical pattern.

## Next Milestones

1. Convert Colab-exported `.py` scripts into clean `.ipynb` notebooks.
2. Save all result tables into `results/` as summary CSV files.
3. Add pipeline figures under `figures/`.
4. Run leave-one-site-out validation for structural MRI models.
5. Run fMRI graph models across all available sites, not only NYU.
6. Compare GNN against simpler connectivity baselines such as logistic regression and random forest on vectorized FC matrices.
7. Add confidence intervals and fold-wise result tables for every major experiment.
