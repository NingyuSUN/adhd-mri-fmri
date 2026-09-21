# Portfolio Case Study: ADHD-200 MRI/fMRI Deep Learning

## Elevator pitch

I built an end-to-end medical-imaging deep-learning project using the multi-site ADHD-200 dataset. The work covers structural MRI and resting-state fMRI data engineering, neuroimaging preprocessing, CNN/GNN/Transformer representations, subject-level evaluation, confound analysis, motion robustness, and reproducible training and verification workflows.

The project demonstrates not only model implementation, but also the ability to detect data leakage and shortcut learning—two of the most important practical risks in medical AI.

## Problem

ADHD is clinically heterogeneous, and ADHD-200 combines scans from multiple hospitals, scanners, acquisition protocols, and demographic distributions. The technical challenge was to determine whether image-derived representations could classify ADHD while separating biological signal from site, age, sex, motion, and quality-control effects.

## What I built

### Data pipeline

- discovered structural MRI and fMRI files across BIDS-like site directories
- recovered and normalized phenotypic labels
- removed duplicates and enforced subject-level identifiers
- implemented QC and motion summaries
- cached registration, ROI time series, feature banks, embeddings, and results in Google Drive
- added checkpointing so long-running compute jobs could resume safely

### Structural MRI branch

- single-slice and multi-slice CNN baselines
- MNI152 registration and Harvard-Oxford ROI-guided slice selection
- subject-level slice aggregation
- ablations for ROI choice, registration, normalization, and aggregation
- pretrained Swin-T transfer experiment
- ComBat and ROI-feature baselines

### fMRI branch

- A424 atlas time-series extraction
- functional-connectivity matrices and ROI summaries
- high-dimensional edge features with training-only feature selection
- frequency/spectral representations
- graph neural network prototype
- frozen BrainLM embeddings
- end-to-end A424 temporal 1D-CNN and Transformer models
- frame scrubbing, motion-restricted cohorts, and spatial network modules

### Evaluation and reliability

- subject-level splitting to prevent slice/time-window leakage
- repeated site-and-label-stratified cross-validation for within-dataset generalization
- nested leave-one-site-out evaluation as a domain-shift stress test
- preprocessing, feature selection, and residualization fit on training folds only
- comparison with age, sex, site, motion, and QC baselines
- paired bootstrap confidence intervals and site-wise analysis

## Key technical decisions

1. **Subject is the split unit.** All slices and fMRI windows belonging to one subject stay in the same fold.
2. **Confounds are explicit baselines.** A high image-model score is not accepted unless it improves over demographic and acquisition variables.
3. **Preprocessing is fold-local.** Scaling, imputation, feature selection, harmonization, and residualization never use test-fold statistics.
4. **Model complexity is staged.** Frozen pretrained representations are evaluated before expensive fine-tuning.
5. **Results are checkpointed.** Long-running preprocessing can resume without repeating completed subjects.

## Results and interpretation

The mixed-site benchmark used 409 subjects and repeated four-fold cross-validation stratified jointly by site and diagnosis. Five repeats produced 20 outer evaluations, with regularization selected inside each training fold.

| Feature set | Mean AUC ± SD |
|---|---:|
| age + sex + motion/QC | 0.677 ± 0.058 |
| motion/QC | 0.641 ± 0.057 |
| confounds + BrainLM | 0.619 ± 0.040 |
| FC + BrainLM | 0.595 ± 0.031 |
| FC ROI summary | 0.583 ± 0.036 |
| spectral | 0.570 ± 0.035 |
| frozen BrainLM | 0.529 ± 0.043 |

The project produced above-chance within-dataset image experiments, but the strongest result still came from demographic and motion/QC variables. Strict site-held-out evaluation then revealed substantial domain shift: in fMRI LOSO the same confound baseline reached 0.686 while frozen BrainLM reached 0.512. Structural Swin-T similarly underperformed its demographic baseline in strict LOSO.

This is an important medical-AI result: model architecture alone cannot compensate for heterogeneous acquisition and confounded labels. The work demonstrates the ability to diagnose why a model fails, not just train it.

The portfolio claim is therefore about engineering and experimental skill—not clinical accuracy: I implemented multiple deep-learning representations, designed leakage-safe comparisons, ran robustness analyses, and interpreted negative evidence responsibly.

## Confirmatory statistics and self-audit (analysis v2)

A follow-up round treated the fusion result as a hypothesis to confirm, not a finding to report as-is:

- **Pre-registered a protocol before running anything**: a symmetric primary contrast, a Nadeau–Bengio corrected confidence interval for the cross-validation estimate, and a pre-registered TOST equivalence test (±0.02 AUC) with a mutually-exclusive, exhaustive decision rule.
- **Had the protocol reviewed by an independent model (Gemini 3.1 Pro) before running it** — the review caught a real overlap bug in the decision table and an invalid statistical-design choice (a 7-cluster bootstrap), both fixed pre-registration.
- **Ran a full strict leave-one-site-out re-analysis** alongside the cross-validation, then **audited my own result** when the two frameworks disagreed, rather than reporting the more favorable one.
- **Found and published a correction to my own published number**: I had reported one site's contribution to the leave-one-site-out estimate as "~40% of subjects", which conflated participant share with the actual AUC pair-weight; the corrected figure is 67.07%. The correction, its derivation, and its effect on every downstream claim are committed to the repository (`docs/paper/STATISTICAL_INTERPRETATION.md`) rather than silently edited away.
- **Self-audited against TRIPOD+AI**, the published reporting standard for AI clinical-prediction studies, to map exactly what a submission-ready manuscript would still need (`docs/paper/TRIPOD_AI_GAPS_20260914.md`).

This is the part of the project I'd point to first in an interview about statistical rigor: not that the numbers looked clean, but that the process was built to catch — and publicly correct — my own mistakes before anyone else had to.

## Technologies

Python, NumPy, pandas, SciPy, scikit-learn, TensorFlow/Keras, PyTorch, PyTorch Geometric, Hugging Face Transformers, nibabel, nilearn, ANTsPy, Google Drive, Linux compute, BIDS-style neuroimaging data, Git/GitHub, GitHub Actions.

## Engineering delivery

The repository also exposes a small aggregate-only quickstart so a reviewer can run a useful path without private ADHD-200 data:

```bash
python tools/portfolio_quickstart.py --output-dir artifacts/portfolio_quickstart
python tools/validate_public_artifacts.py
```

The public artifact validator checks manifest hashes, table/figure counts, CSV schemas, and private-path redaction. GitHub Actions runs the locked statistics tests, quickstart schema check, public-artifact validation, and Python syntax parsing. The full 66-unit replay remains a separately gated workflow because it requires authorized private derivatives.

## Interview discussion points

- why slice-level random splitting creates subject leakage
- why mixed-site CV and unseen-site testing answer different questions
- why accuracy can be misleading under site/class imbalance
- how training-only residualization and feature selection prevent leakage
- why a confound-only model can outperform MRI/fMRI
- when pretrained Transformer fine-tuning is or is not justified
- how checkpointing and caching make large neuroimaging workflows practical on remote compute

## Responsible-use statement

This is a research and portfolio project. It is not a clinical diagnostic tool and must not be used for screening, treatment decisions, or individual risk prediction.
