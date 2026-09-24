## Current 378-person fMRI evidence

`fmri_378/` holds independently replayed aggregate outputs, selected alphas, learning curves and an explicit verification record. See [current overview](../README.md). No subject-level predictions are committed. Existing tables below are historical or separate structural experiments.

# Aggregate Results

This folder contains small, non-identifying summary tables for the locked final fMRI benchmark.

| File | Contents |
|---|---|
| `structural_mri_summary.csv` | locked structural MRI results and matched baselines |
| `fmri_benchmark_stratified_cv_summary.csv` | repeated site+label-stratified 4-fold CV, five repeats |
| `fmri_mixed_site_model_sweep_cv.csv` | follow-up mixed-site logistic/SVM/MLP comparison |
| `fmri_mixed_site_model_sweep_holdout.csv` | pre-specified 80/20 comparison split |
| `fmri_end_to_end_summary.csv` | image-only A424 1D-CNN and temporal Transformer summary |
| `fmri_end_to_end_fold_metrics.csv` | fold-level end-to-end neural-network metrics |
| `fmri_strict_loso_summary.csv` | primary `n=409` nested LOSO comparison |
| `fmri_robustness_summary.csv` | motion-restricted, residualized, and within-site analyses |
| `fmri_motion_scrubbing_summary.csv` | strict stage-3 `n=246` model comparison |
| `fmri_motion_scrubbing_bootstrap.csv` | paired subject bootstrap estimates and intervals |
| `structural_functional_fusion_summary.csv` | QC-locked structural/functional/fusion paired analysis, 17 models × 3 cohorts, mean over 5 repeats |
| `structural_functional_fusion_paired_deltas.csv` | prespecified paired AUC / within-site deltas for the same analysis |

Subject-level predictions, time series, embeddings, and large arrays are intentionally excluded. The authoritative narrative interpretation is in `../RESULTS.md` and `../FINAL_REPORT.md`.
