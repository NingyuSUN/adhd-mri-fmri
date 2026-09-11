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
| `v2_cv_contrast_stats.csv` | analysis v2: mixed-site CV paired deltas with Nadeau–Bengio 90% intervals (df 14 and conservative df 2) |
| `v2_loso_contrast_stats.csv` | analysis v2: strict LOSO paired deltas (pair-weighted / macro) with site-stratified subject-bootstrap 90% intervals |
| `v2_loso_per_site_deltas.csv` | analysis v2: per-held-out-site ΔAUC and within-site bootstrap 95% CI (forest plot F1) |
| `v2_calibration_summary.csv` | analysis v2: ECE, Brier, Brier skill score for four report models × three cohorts |

Subject-level predictions, time series, embeddings, and large arrays are intentionally excluded. The authoritative narrative interpretation is in `../RESULTS.md` and `../FINAL_REPORT.md`.
