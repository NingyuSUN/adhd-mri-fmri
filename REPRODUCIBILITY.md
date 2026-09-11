# Reproducibility Guide

For the current multimodal v2 workflow, use [the complete reproduction package](reproduction/README.md). The legacy notebook instructions below concern earlier rounds. Reproduction levels and measured outcomes are documented separately; saved-prediction recomputation is not model retraining.

## Final analysis order

The original structural and graph prototypes are stored in `notebooks/`. The final fMRI analysis is represented by four Colab notebooks:

1. [06 — strict LOSO benchmark](https://colab.research.google.com/drive/1Zkrj4btEB2YrWDjYOx9vmlLCvHxPrCfM)
2. [07 — site/motion robustness](https://colab.research.google.com/drive/1jdFe7GRn7mIKcVtGig7_66qdZhbBsnqe)
3. [08 — motion scrubbing and spatial modules](https://colab.research.google.com/drive/12ez3NKRvs88YrmLIfNT-tNgBcU3MpbzE)
4. [09 — repeated site-and-label-stratified portfolio benchmark](https://colab.research.google.com/drive/1CkXQKR3tfbdIsuM41ML1YNPULmv9HFU2)

Notebook 06 defines the locked unseen-site benchmark. Notebook 07 tests residualization and within-site behavior. Notebook 08 performs the strict motion-scrubbing and spatial-module analysis. Notebook 09 provides the presentation-friendly within-dataset comparison with 20 outer evaluations.

## Expected Drive locations

```text
/content/drive/MyDrive/ADHD200-data/
/content/drive/MyDrive/ADHD200-data/fmri/brainlm_a424/
/content/drive/MyDrive/ADHD200-data/fmri/strict_loso_benchmark/
/content/drive/MyDrive/ADHD200-data/fmri/strict_loso_benchmark/stage3_scrubbing_network/
/content/drive/MyDrive/ADHD200-data/fmri/portfolio_site_stratified_cv/
```

Large arrays and subject-level predictions remain in Drive. Only aggregate, non-identifying tables are committed to `results/`.

## Leakage controls

- one subject appears in only one evaluation partition
- test sites are never used for fitting preprocessing
- feature scaling is fit on training data
- feature selection is fit on training data
- confound residualization is fit on training data
- hyperparameters are selected inside training sites
- held-out site predictions are saved once per outer fold

## Primary metric

For portfolio presentation, the primary within-dataset metric is mean AUC across 20 outer folds from repeated site-and-label-stratified CV. For the unseen-site stress test, macro AUC is the unweighted mean of valid held-out-site AUC values. These metrics answer different questions and must not be substituted for each other.

## Randomness

The notebooks use fixed seeds where supported. Bootstrap analyses use a fixed generator seed. Exact floating-point values can vary slightly across Colab library or GPU versions; the scientific conclusion should be evaluated from the full comparison pattern, not the final decimal place.

## Verification checklist

- [x] subject-level splitting
- [x] repeated site-and-label-stratified CV
- [x] strict site-held-out evaluation
- [x] training-only preprocessing
- [x] nested model selection
- [x] non-image confound baselines
- [x] fold/site-level metrics
- [x] motion-restricted analysis
- [x] training-fold residualization
- [x] within-site analysis
- [x] frame scrubbing
- [x] paired bootstrap uncertainty
- [x] aggregate result tables
- [x] limitations and model card

## Reproducing the final claim

Reproduction does not require the exact same winning regularization parameter. It requires recovering the qualitative result that confound-only features outperform tested image-only representations and that imaging features do not add stable cross-site value.
