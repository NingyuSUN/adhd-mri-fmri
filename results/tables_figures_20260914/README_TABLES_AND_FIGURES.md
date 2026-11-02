# Tables and figures — 2026-09-14

Purpose: this document collects the definitions behind the tables and the figure captions, as a reference for manuscript writing and result checking. ADHD-200 data use terms are in the repository's docs/DATA.md. This page is not manuscript text, is not for clinical diagnosis, and involves no new model training.

## Table definitions

- Table1: primary cohort, grouped by the frozen binary label; mean (sample SD) or median [Q1, Q3]. Continuous values are observed values before imputation, with the number missing listed alongside; the denominator for categorical percentages is the column total.
- Age and sex use the actual model inputs participant_age / participant_sex_male. This is recorded sex, not gender identity. Following the project mapping, label 1 is called ADHD and label 0 control; clinical diagnoses were not independently re-reviewed.
- Head-motion pct_fd_gt_0p2 is stored as a 0–1 proportion and shown as a percentage (×100); TIV is converted from mm³ to mL (÷1000). FD/DVARS keep their metadata scale; their acquisition and computation units must be confirmed before formal submission. No participants were removed as outliers.
- Table2: CV is the mean fold AUC, aggregated over repeats; it is not an AUC computed on all repeated predictions pooled together. LOSO pair-weighted and equal-site macro averages are listed separately and are not interchangeable. The seven displayed models are fixed by research role; the full table of 17 outputs is TableS2 and was not filtered by score.
- Table3: the primary contrast with its original intervals; TableS7/S8 are interval sensitivity analyses added later and are not the same bootstrap.
- Table4/TableS3: post hoc descriptive decompositions. All QC cohorts overlap; no independent between-group tests were run.
- TableS5: training/validation/test counts listed for the 66 units; their sum cannot be read as a number of participants.

## Method boundaries

LOSO used a single 85/15 split within the six training sites and did not refit on all six sites after selection. The current results reflect this pipeline as executed. Full reproduction starts only from the frozen time series and volume derivatives; raw MRI preprocessing, complete expert QC and external validation are not established by it.

## Figure captions

### Figure1_participant_flow

QC flow starting from the verified paired cohort of 378 participants. Three failed image quality; the remaining 375 form the include-HOLD cohort. Excluding 25 HOLD cases gives the primary cohort of 350; excluding a further 48 signal warnings gives the warning-free cohort of 302. The three cohorts overlap. QC was a sampled assisted review, not an expert full-volume assessment. Earlier recruitment and screening steps are not reconstructed in this figure.

### Figure2_primary_contrast

Primary contrast: full_fusion_structural_mlp − full_functional_mlp. CV shows the mean of the 15 fold differences with the original corrected-t 90% interval; LOSO shows the within-site case–control pair-weighted ΔAUC with the original 90% interval from 10,000 within-site subject bootstrap draws. The grey band marks ±0.02. The two intervals rest on different conditions; the LOSO interval does not include uncertainty from retraining or from sampling new sites.

### Figure3_QC_decomposition

Post hoc decomposition of the change across QC cohorts. Using common test participants and fixed primary-cohort site weights, it separates the contributions of the fitting pipeline, the evaluated sample composition and the site weights. The components reconstruct the total difference exactly; this is a descriptive decomposition, not a causal effect.

### Figure4_NYU_selector_stability

Selection stability of the final structural fusion weight for the NYU held-out fold, from 1,000 bootstrap draws by site and label within the internal validation sets of the remaining training sites only; fitted models, upstream weights and early stopping were held fixed. This is not tuning on NYU test data and not a whole-pipeline confidence interval.

### FigureS1_CV_models

The seven primary-cohort models shown by fixed research role, matching Table2. Points are mean fold AUC; error bars span the minimum to the maximum of the five repeat means and are not confidence intervals. All 17 outputs are listed in TableS2.

### FigureS2_calibration

Descriptive calibration curves for the frozen repeated-CV predictions. The primary-cohort n=1750 means five predictions for each of 350 participants, not 1,750 independent participants. Weighted training outputs are not validated individual diagnostic risks.

### FigureS3_site_contributions

Site contributions to the pair-weighted result. NYU accounts for 39.7% of primary-cohort participants but 67.07% of the within-site positive–negative pair weight; its primary-cohort structural increment is zero, so the overall positive increment cannot be attributed to NYU.

### FigureS4_CV_interval_sensitivity

Post hoc interval sensitivity to the degrees-of-freedom and test/fit-ratio conventions. All intervals come from the same set of results; they are not independent replications.

### FigureS5_LOSO_contrasts

Estimates of the primary structural increment by site and QC cohort; error bars are the original 95% within-site subject bootstrap intervals, which differ from the overall 90% intervals in Figure2. Intervals are conditional on the observed sites and frozen models; small-site estimates are imprecise, and the executed LOSO did not refit on all training sites after selection.


## Files and reproduction

Open index.html to view all main tables and figures; tables holds editable CSVs; figures holds PNG/PDF files; source_aggregates holds the newly compiled aggregates and frozen input hashes; source_results holds the numerical sources of existing figures and tables. scripts is a snapshot of the code used for this compilation; its participant aggregation step needs the original project paths and server inputs. The exported package contains no individual records or raw images.

source_results/original_cv_contrast_stats.csv and original_loso_contrast_stats.csv support Figure2/Table3; qc_decomposition.csv supports Figure3/Table4; selector_alpha_distribution.csv supports Figure4; original_cv_primary_summary.csv supports FigureS1; original_calibration.csv supports FigureS2; site_contributions.csv supports FigureS3; cv_interval_audit.csv supports FigureS4; original_loso_per_site_deltas.csv supports FigureS5. No analysis parameters were re-selected for presentation.

Validation: participant group counts, weighted means, the 21 existing site/cohort counts, input hashes, CSV structure and HTML links all pass; all 9 figures were inspected individually. The original historical figures and frozen runs were not overwritten.
