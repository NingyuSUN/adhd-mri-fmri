# Final Results

## Portfolio benchmark

The portfolio-facing endpoint is mean AUC across repeated four-fold cross-validation stratified jointly by site and diagnosis (`n=409`, five repeats, 20 outer evaluations). Imputation, scaling, and logistic-regression regularization selection are refit inside the training data of every outer fold.

| Rank | Feature set | Mean AUC | SD | Mean AP | Mean balanced accuracy |
|---:|---|---:|---:|---:|---:|
| 1 | age + sex + motion/QC | 0.677 | 0.058 | 0.642 | 0.613 |
| 2 | motion/QC | 0.641 | 0.057 | 0.608 | 0.605 |
| 3 | confounds + BrainLM | 0.619 | 0.040 | 0.587 | 0.583 |
| 4 | FC + BrainLM | 0.595 | 0.031 | 0.555 | 0.570 |
| 5 | FC ROI summary | 0.583 | 0.036 | 0.533 | 0.555 |
| 6 | age + sex | 0.573 | 0.047 | 0.507 | 0.587 |
| 7 | spectral | 0.570 | 0.035 | 0.513 | 0.563 |
| 8 | frozen BrainLM | 0.529 | 0.043 | 0.505 | 0.537 |

These scores measure within-ADHD-200 discrimination when every fold contains all sites; they are not estimates for deployment at an unseen hospital. The primary robustness endpoint remains macro AUC across evaluable held-out sites under strict nested LOSO, with all preprocessing and model selection fit on training sites only.

### Follow-up mixed-site model sweep

A fixed follow-up comparison evaluated logistic regression, RBF-SVM, and a shallow MLP on the combined FC, spectral, and BrainLM feature bank. Repeated CV was best for site + confounds (0.693 ± 0.025). The strongest fMRI-inclusive and fMRI-only models were RBF-SVM at 0.624 ± 0.027 and 0.622 ± 0.027, respectively. On the pre-specified 80/20 split, site + confounds reached 0.709 while the best fMRI-inclusive model reached 0.576. None matched the structural Swin-T single-split reference of 0.774.

### End-to-end A424 time-series networks

Compact image-only networks were trained directly on 192×424 standardized parcel time series using four subject-level folds jointly stratified by site and diagnosis. Early stopping used a validation subset drawn only from the outer training fold.

| Model | Mean AUC ± SD | Mean AP | Mean balanced accuracy | Best single fold |
|---|---:|---:|---:|---:|
| 1D-CNN | 0.580 ± 0.057 | 0.548 | 0.532 | 0.644 |
| temporal Transformer | 0.578 ± 0.056 | 0.530 | 0.560 | 0.636 |

Neither model passed the pre-specified image-only baseline of 0.622. The experiment nevertheless completes the end-to-end deep-learning branch without demographic, motion, QC, or site inputs.

## Structural MRI

The structural branch included single-slice, multi-slice, ROI-guided, ComBat/ROI-feature, pretrained Swin-T, ablation, site-bias, and strict LOSO analyses.

| Evaluation | Model | N | AUC | Comparator/interpretation |
|---|---|---:|---:|---|
| Strict LOSO OOF | ROI-guided CNN | 924 | 0.470 | unstable site-wise AUCs, 0.397–0.663 |
| Strict LOSO OOF | pretrained Swin-T MRI | 923 | 0.579 | 95% CI 0.543–0.617 |
| Strict LOSO OOF | age + sex logistic | 923 | 0.619 | 95% CI 0.584–0.656; exceeds Swin-T |
| Five-fold OOF | raw ROI logistic | 923 | 0.601 | less stringent than site-held-out evaluation |
| Five-fold OOF | ComBat ROI logistic | 923 | 0.536 | harmonization did not improve AUC |
| Single held-out split | pretrained Swin-T MRI | 185 | 0.774 | age + sex + site baseline was 0.781 |

The apparently strong single-split Swin-T result is not evidence of a structural biomarker because the matched non-image baseline performs better, and strict site-held-out performance falls to 0.579. The structural conclusion is negative: no stable out-of-site anatomical predictor was established.

## fMRI: locked full cohort

`n=409` subjects from sites with both classes in the held-out test set.

| Rank | Feature set | Macro LOSO AUC | Interpretation |
|---:|---|---:|---|
| 1 | age + sex + motion/QC | 0.686 | strongest result; non-image confounds |
| 2 | motion/QC | 0.664 | motion/QC alone is strongly predictive |
| 3 | confounds + BrainLM | 0.622 | lower than confounds alone |
| 4 | age + sex | 0.583 | demographic signal |
| 5 | BrainLM frozen | 0.512 | approximately chance |
| 6 | FC + BrainLM | 0.501 | approximately chance |
| 7 | spectral | 0.492 | approximately chance |
| 8 | FC ROI summary | 0.477 | below chance |
| 9 | full FC edges, top 2000 | 0.430 | below chance |

The decisive comparison is not BrainLM versus 0.5; it is BrainLM versus the confound baseline. Adding BrainLM reduced macro AUC from 0.686 to 0.622, so there is no demonstrated incremental predictive value.

## fMRI: motion-restricted cohort

`n=351`.

| Feature set | Macro LOSO AUC |
|---|---:|
| confounds | 0.657 |
| confounds + spectral | 0.564 |
| confounds + BrainLM | 0.532 |
| BrainLM | 0.406 |

Motion restriction did not uncover hidden BrainLM signal.

## fMRI: training-fold residualization

Residualization models were fit only on training subjects inside each LOSO fold.

| Feature set | Macro LOSO AUC |
|---|---:|
| confounds + residualized BrainLM | 0.605 |
| confounds + residualized spectral | 0.545 |
| confounds + residualized FC | 0.494 |
| residualized spectral | 0.490 |
| residualized BrainLM | 0.475 |
| residualized FC | 0.461 |

Residualization did not create a stable image-only predictor. The best combined result still underperformed the original confound-only baseline.

## fMRI: within-site validation

| Feature set | Macro within-site AUC |
|---|---:|
| confounds | 0.663 |
| confounds + BrainLM | 0.574 |
| spectral | 0.501 |
| FC | 0.459 |
| BrainLM | 0.443 |

The failure is not explained solely by unseen-site shift; image features also perform weakly within sites.

## fMRI: strict motion scrubbing and spatial modules

The strict stage-3 cohort contains `n=246` subjects after motion/QC restrictions.

| Feature set | Macro LOSO AUC |
|---|---:|
| confounds | 0.622 |
| original FC summary | 0.532 |
| scrubbed FC summary | 0.506 |
| confounds + scrubbed FC | 0.490 |
| original spatial modules | 0.493 |
| scrubbed spatial modules | 0.441 |
| confounds + scrubbed spatial modules | 0.541 |

Paired subject bootstrap estimates:

| Contrast/model | Estimate | 95% CI |
|---|---:|---:|
| original FC | 0.533 | 0.399 to 0.660 |
| scrubbed FC | 0.507 | 0.408 to 0.623 |
| scrubbed FC − original FC | -0.026 | -0.149 to 0.072 |
| scrubbed FC − confounds | -0.113 | -0.254 to 0.038 |

The confidence intervals include no improvement. Scrubbing does not rescue the imaging model.

## Symptom regression

Among `n=277` subjects with symptom measures, macro site-wise Pearson correlation was approximately 0.19, while pooled correlation was approximately zero and unstable. This is insufficient evidence for a generalizable symptom prediction model.

## Final interpretation

The experiments consistently show stronger signal in age, sex, head motion, and QC than in structural or functional neuroimaging representations. No tested MRI/fMRI model provides stable incremental information beyond these confounds. The project therefore supports a careful negative/boundary conclusion rather than a diagnostic claim.
