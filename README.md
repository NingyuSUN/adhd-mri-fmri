# ADHD-200 MRI/fMRI Classification

This portfolio project demonstrates an end-to-end deep-learning workflow for structural MRI and resting-state fMRI: data engineering, neuroimaging preprocessing, CNN/GNN/Transformer modeling, leakage-safe evaluation, robustness analysis, and reproducible Colab execution.

**Project status: completed deep-learning case study.** The technical objective is to demonstrate the ability to build and evaluate real medical-AI pipelines—not to claim a clinically deployable ADHD diagnostic system.

## Portfolio highlights

| Area | Demonstrated work |
|---|---|
| Data engineering | Multi-site BIDS discovery, phenotypic-label recovery, subject deduplication, QC, caching, checkpointed Google Drive pipelines |
| Structural MRI | Slice and ROI pipelines, MNI registration, CNNs, pretrained Swin-T, ComBat and ablation studies |
| Functional MRI | A424 time-series extraction, functional connectivity, spectral features, motion scrubbing, network modules |
| Deep learning | 2D/3D CNN concepts, GNN prototypes, frozen BrainLM transfer learning, Transformer comparison |
| Evaluation | Subject-level splits, site-stratified CV, nested LOSO stress testing, bootstrap uncertainty, confound baselines |
| Research practice | Leakage prevention, reproducibility, model card, limitations, clinically responsible interpretation |

```mermaid
flowchart LR
    A[ADHD-200 MRI/fMRI] --> B[Manifest and QC]
    B --> C1[T1 registration and ROI slices]
    B --> C2[A424 fMRI time series]
    C1 --> D1[CNN / Swin-T]
    C2 --> D2[FC / spectral / GNN]
    C2 --> D3[BrainLM embeddings]
    D1 --> E[Subject-level evaluation]
    D2 --> E
    D3 --> E
    E --> F[Confound comparison and robustness]
```

For a concise portfolio narrative and interview-ready discussion, see [PORTFOLIO_CASE_STUDY.md](PORTFOLIO_CASE_STUDY.md).

## Scientific outcome

The analyses do not support a reliable cross-site ADHD predictor from the available MRI/fMRI representations.

- In the portfolio-oriented repeated 4-fold site-and-label-stratified CV (`5` repeats, `20` outer evaluations, `n=409`), age + sex + motion/QC reached mean AUC **0.677 ± 0.058**.
- The strongest image-only/representation result in that experiment was FC + frozen BrainLM at **0.595 ± 0.031**; FC ROI summary reached **0.583 ± 0.036**, spectral features **0.570 ± 0.035**, and frozen BrainLM alone **0.529 ± 0.043**.
- A follow-up end-to-end experiment trained a 1D-CNN and temporal Transformer directly on standardized A424 parcel time series. Their four-fold mean AUCs were **0.580 ± 0.057** and **0.578 ± 0.056**, below the locked image-only RBF-SVM baseline of **0.622**.
- Structural MRI also failed the strict generalization test: Swin-T reached LOSO OOF AUC **0.579** versus **0.619** for age + sex, while the ROI-guided CNN reached **0.470**.
- In the locked fMRI cohort (`n=409`), age + sex + motion/QC reached macro LOSO AUC **0.686**.
- The best tested image-only fMRI result was frozen BrainLM at **0.512** macro LOSO AUC; spectral, FC-summary, and full-edge models were approximately chance or worse.
- Adding BrainLM to confounds reduced performance from **0.686** to **0.622**.
- Training-fold residualization, within-site validation, strict motion restriction, frame scrubbing, and spatial network aggregation did not reveal a stable image-derived gain.

The defensible interpretation is that the dataset contains strong demographic/site/motion structure, while the tested neuroimaging features do not generalize reliably to unseen sites.

## Headline fMRI results

| Evaluation | Model | N | AUC |
|---|---|---:|---:|
| Repeated site+label-stratified CV | age + sex + motion/QC | 409 | 0.677 ± 0.058 |
| Repeated site+label-stratified CV | FC + BrainLM | 409 | 0.595 ± 0.031 |
| Repeated site+label-stratified CV | FC ROI summary | 409 | 0.583 ± 0.036 |
| Repeated site+label-stratified CV | BrainLM frozen | 409 | 0.529 ± 0.043 |
| Strict nested LOSO | age + sex + motion/QC | 409 | 0.686 |
| Strict nested LOSO | motion/QC | 409 | 0.664 |
| Strict nested LOSO | age + sex | 409 | 0.583 |
| Strict nested LOSO | BrainLM frozen | 409 | 0.512 |
| Strict nested LOSO | FC + BrainLM | 409 | 0.501 |
| Strict nested LOSO | spectral | 409 | 0.492 |
| Strict nested LOSO | FC ROI summary | 409 | 0.477 |
| Strict nested LOSO | full FC edges, top 2000 | 409 | 0.430 |
| Strict nested LOSO | confounds + BrainLM | 409 | 0.622 |

See [RESULTS.md](RESULTS.md) and [FINAL_REPORT.md](FINAL_REPORT.md) for the full interpretation and robustness analyses.

## Evaluation strategy

For portfolio presentation, the primary within-dataset experiment uses repeated site-and-label-stratified subject-level cross-validation. The completed LOSO analysis is retained as an advanced domain-shift stress test rather than the only definition of project success.

- Splits are performed by subject, never by slice or time window.
- The portfolio benchmark uses repeated four-fold CV stratified jointly by site and label; imputation, scaling, and regularization selection are fit inside each training fold.
- The reported portfolio number is the mean AUC across 20 outer folds, with standard deviation across folds.
- LOSO is reported separately as an unseen-site stress test; held-out sites are not used for scaling, feature selection, residualization, or hyperparameter selection.
- Every image model is compared with non-image confound baselines.
- A model is not considered useful merely because its AUC is above 0.5; it must add stable out-of-site information beyond confounds.

## Analysis sequence

The repository contains the original structural and connectivity prototypes. The final fMRI benchmark was completed in Colab:

1. [06 — strict LOSO benchmark](https://colab.research.google.com/drive/1Zkrj4btEB2YrWDjYOx9vmlLCvHxPrCfM)
2. [07 — site/motion robustness](https://colab.research.google.com/drive/1jdFe7GRn7mIKcVtGig7_66qdZhbBsnqe)
3. [08 — motion scrubbing and spatial modules](https://colab.research.google.com/drive/12ez3NKRvs88YrmLIfNT-tNgBcU3MpbzE)
4. [09 — portfolio site-stratified CV](https://colab.research.google.com/drive/1CkXQKR3tfbdIsuM41ML1YNPULmv9HFU2) — one-click comparison with completed outputs
5. [10 — mixed-site fMRI model sweep](https://colab.research.google.com/drive/1Qh2aAzmHQTMMQl_SMF7JPY_ibTf3HYcJ) — logistic, RBF-SVM, and MLP comparison with site/confound ablations
6. [11 — A424 end-to-end CNN/Transformer](https://colab.research.google.com/drive/142dwSF1fV7d1khI2l8JADhMbtXwEcv8M) — direct time-series neural networks with completed four-fold outputs

Small aggregate result tables are versioned in `results/`. Subject-level predictions and large intermediate arrays remain in Google Drive and are not committed.

## Repository structure

```text
adhd-mri-fmri/
├── README.md
├── FINAL_REPORT.md
├── MODEL_CARD.md
├── PROJECT_STATUS.md
├── METHODS.md
├── RESULTS.md
├── LIMITATIONS.md
├── REPRODUCIBILITY.md
├── DATA.md
├── notebooks/              # original Colab-exported pipelines
├── results/                # small aggregate result tables
├── docs/
├── figures/
├── src/
└── utils/
```

## Data

The project uses the ADHD-200 multi-site dataset:

- T1-weighted structural MRI
- resting-state fMRI derivatives
- phenotypic labels and demographic variables
- motion and QC measurements where available

Raw data are not included. The final fMRI outputs are stored under:

```text
<DATA_DIR>/fmri/strict_loso_benchmark/
```

See [DATA.md](DATA.md) for the expected layout.

## Reuse

The code and result tables can be used as a benchmark for confound-aware neuroimaging classification. They must not be presented as a clinical ADHD diagnostic system.

## Author and license

Ningyu Sun. Code is released under the MIT License; ADHD-200 data remain subject to their original terms.
