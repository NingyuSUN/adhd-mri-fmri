# Results

Expected output files produced by the notebooks.

## T1w CNN Pipeline

| File | Description |
|------|-------------|
| `roi_guided_results_5fold_oof.csv` | Per-fold and OOF subject-level AUC |
| `preds_subject_fold{1..5}.csv` | Subject-level predictions per fold |
| `error_analysis_outputs/subject_error_table.csv` | TP/TN/FP/FN per subject |
| `error_analysis_outputs/site_performance.csv` | AUC, accuracy, error rate per site |
| `error_analysis_outputs/confident_FP.csv` | False positives with prob ≥ 0.80 |
| `error_analysis_outputs/confident_FN.csv` | False negatives with prob ≤ 0.20 |

## fMRI GNN Pipeline

| File | Description |
|------|-------------|
| `preds_subject_all_folds.csv` | All-fold subject predictions |
| `processed_data/full_ts_dict.pkl` | Cached ROI time series (all subjects) |
| `processed_data/full_labels_dict.pkl` | Cached subject labels |
