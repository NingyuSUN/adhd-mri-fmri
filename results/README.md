# Results Folder

Store only small, summary-level result files here. Do not commit subject-level raw predictions if they expose restricted metadata.

Recommended files:

```text
t1_single_slice_summary.csv
t1_multislice_summary.csv
t1_roi_guided_summary.csv
t1_ablation_results.csv
site_bias_baselines.csv
fmri_gnn_summary.csv
foldwise_metrics.csv
```

Every result table should include:

- experiment name
- split strategy
- number of subjects
- number of sites
- AUC
- confidence interval if available
- notes on confound controls
