# Methods

This document describes the methodology actually used to produce the results in
[RESULTS.md](RESULTS.md) and [FINAL_REPORT.md](FINAL_REPORT.md). It supersedes the
project's original single-slice/ROI-CNN-only plan; later branches (frozen BrainLM,
Swin-T transfer, structural+functional fusion, the v2 statistical framework)
replaced or extended the initial design as the project progressed.

## Overview

The analysis has three model branches evaluated under two evaluation frameworks:

1. **Structural MRI** — T1-weighted volume/slice-based models.
2. **Resting-state fMRI** — functional-connectivity, spectral, graph, and
   pretrained-embedding models built on A424 parcel time series.
3. **Structural + functional late fusion** — models that combine both modalities
   with non-imaging confounds, trained and evaluated together on one frozen protocol.

Every branch is compared against non-imaging confound baselines (age, sex, site,
head motion/QC), and every split is performed at the subject level so that no
slice, time window, or repeated measurement crosses a train/test boundary.

---

## Structural MRI branch

1. **Single-slice CNN baseline.** One middle axial T1 slice per subject, resized
   to 128×128, trained with a small 2D CNN. Validates the data pipeline and gives
   a conservative lower bound.
2. **Multi-slice CNN.** Multiple axial slices per subject from the central
   30–70% z-range; subject-level predictions are the mean of slice-level
   probabilities. Subjects are split before slices are extracted.
3. **ROI-guided CNN.** Each subject is rigidly registered to the MNI152 2mm
   template; Harvard-Oxford cortical/subcortical masks (frontal cortex,
   anterior/posterior cingulate, thalamus, caudate, putamen, pallidum,
   accumbens) select slices with high ROI coverage. Slices are z-score
   normalized before training.
4. **ROI-feature and ComBat baselines.** Regional volume/TIV fractions (68
   cortical + 30 subcortical/CSF regions) as tabular logistic-regression
   features, with and without ComBat site harmonization.
5. **Pretrained Swin-T transfer.** A frozen Swin-T representation evaluated
   both on a single held-out split and under strict leave-one-site-out (LOSO).

**Ablation factors:** ROI-guided vs. whole-brain/random slice selection, MNI
registration vs. raw subject space, z-score normalization vs. none, mean vs.
max slice-probability aggregation. These test whether performance depends on
the hypothesized ROI signal or on a shortcut (scanner intensity style, site
identity, registration artifacts).

**Result:** no structural configuration produced a predictor that was stable
under strict site-held-out evaluation; the age+sex baseline outperformed every
image model under LOSO (see [RESULTS.md](RESULTS.md#structural-mri)).

---

## Resting-state fMRI branch

1. **Manifest construction.** BIDS discovery of resting-state `bold.nii.gz`
   files, `ses-1` only, subject deduplication, labels merged from
   `participants.tsv` or phenotypic CSVs.
2. **A424 time-series extraction.** ROI-wise time series from the A424 atlas
   (`NiftiLabelsMasker`), standardized and detrended.
3. **Functional connectivity / spectral features.** Full and top-selected
   (ANOVA, training-fold-only) connectivity edges, ROI-summary connectivity,
   and frequency/spectral representations.
4. **Graph neural network prototype.** Nodes = ROIs, edges = functional
   connectivity, node features = ROI-level time-series summaries; a GCN
   (`GCNConv` → ReLU → dropout → global mean pooling → linear classifier) with
   a fixed node set and node order across subjects (no per-subject ROI
   deletion, to avoid inconsistent graph dimensions and sample loss).
5. **Frozen BrainLM embeddings.** A pretrained representation evaluated frozen,
   both alone and concatenated with confounds.
6. **End-to-end temporal models.** A 1D-CNN and a temporal Transformer trained
   directly on standardized 192×424 parcel time series, with no demographic,
   motion, QC, or site inputs.

**Result:** across every representation, non-imaging confounds (age, sex,
motion/QC) outperformed image-derived features under strict LOSO; adding
BrainLM to confounds *reduced* macro AUC (0.686 → 0.622). See
[RESULTS.md](RESULTS.md#fmri-locked-full-cohort).

---

## Confound baselines

Every image model is compared against non-imaging baselines built from the
same subjects: site-only, age+sex, motion/QC, and age+sex+motion/QC combined.
An image model is not treated as evidence of an ADHD-specific signal unless it
outperforms these baselines under the same strict evaluation — in every branch
tested here, none did.

---

## Structural + functional late fusion

A follow-up round retrained structural (98 region/TIV volume fractions),
functional (A424 tangent connectivity), and non-imaging models **together** on
one frozen protocol: three prespecified QC-locked cohorts (`primary` n=350,
`warning_free` n=302, `include_holds` n=375), the original 5-repeat × 3-fold
subject-level split identities, L2 logistic regression (validation-selected C)
and a fixed GELU MLP (3-seed ensemble), and validation-only convex fusion
weights. Full protocol and per-model results:
[docs/structural_functional_fusion.md](docs/structural_functional_fusion.md).

## Evaluation framework

- **Stratified-CV benchmark (primary presentation metric):** repeated four-fold
  cross-validation stratified jointly by site and diagnosis, five repeats (20
  outer evaluations), with imputation, scaling, and hyperparameter selection
  refit inside every training fold.
- **Strict nested leave-one-site-out (LOSO):** an unseen-site robustness stress
  test. Held-out sites are never used for scaling, feature selection,
  residualization, or hyperparameter selection. Macro AUC across evaluable
  held-out sites is the primary LOSO metric so that large sites cannot dominate
  the conclusion.
- **Confirmatory statistics (analysis v2):** a pre-registered protocol
  ([docs/analysis_v2_protocol.md](docs/analysis_v2_protocol.md)) adds a
  Nadeau–Bengio corrected interval for the CV contrast, a pre-registered TOST
  equivalence test (margin ±0.02 AUC), and a site-stratified subject bootstrap
  for LOSO uncertainty. See [docs/analysis_v2_results.md](docs/analysis_v2_results.md)
  and the [statistical interpretation](docs/paper/STATISTICAL_INTERPRETATION.md).

## Leakage-prevention rules

- Subject (not slice, not time window, not repeated visit) is the split unit.
- Preprocessing, feature selection, residualization, harmonization, and
  hyperparameter/architecture selection are fit on the training fold only.
- Held-out LOSO sites contribute no information to any fitted step.
- Aggregate tables never contain `subject_id`, raw file paths, or individual
  predictions (enforced by `tools/validate_public_artifacts.py`).

## Where to find full detail

- Model-by-model numbers: [RESULTS.md](RESULTS.md)
- Narrative conclusion: [FINAL_REPORT.md](FINAL_REPORT.md)
- Fusion protocol and results: [docs/structural_functional_fusion.md](docs/structural_functional_fusion.md)
- v2 pre-registration, deviations, and results: [docs/analysis_v2_protocol.md](docs/analysis_v2_protocol.md), [docs/analysis_v2_deviations.md](docs/analysis_v2_deviations.md), [docs/analysis_v2_results.md](docs/analysis_v2_results.md)
- Reproduction commands: [reproduction/README.md](reproduction/README.md)
