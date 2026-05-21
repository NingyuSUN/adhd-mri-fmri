# Methods

## Overview

The analysis is divided into two branches:

1. T1-weighted structural MRI classification using 2D CNNs.
2. Resting-state fMRI functional connectivity classification using graph neural networks.

Both branches use subject-level evaluation and avoid slice-level leakage.

---

## Structural MRI Branch

### Step 1: Single-slice CNN baseline

Each subject contributes one axial middle slice from the T1-weighted MRI volume.

Processing steps:

1. Read `participants.tsv`.
2. Map diagnosis to binary label.
3. Collect `*_T1w.nii.gz` files from BIDS folders.
4. Merge labels and image paths.
5. Filter anatomical QC pass subjects.
6. Deduplicate to one T1 image per subject.
7. Extract middle axial slice.
8. Resize to 128 × 128.
9. Train a small 2D CNN.
10. Evaluate using AUC, confusion matrix, recall, precision, and threshold analysis.

### Step 2: Multi-slice CNN baseline

Each subject contributes multiple axial slices sampled from the middle z-range, usually 30%–70% of the volume.

Key rule:

> Split train/test by subject first, then extract slices within each split.

Final prediction is obtained by mean aggregation of slice-level probabilities.

### Step 3: ROI-guided CNN

The ROI-guided branch introduces neuroanatomical priors.

Processing steps:

1. Load MNI152 2mm template.
2. Fetch Harvard-Oxford cortical and subcortical atlases.
3. Define ADHD-relevant ROI mask:
   - frontal cortex
   - anterior/posterior cingulate
   - paracingulate
   - thalamus
   - caudate
   - putamen
   - pallidum
   - accumbens
4. Register each subject T1 image to MNI152 2mm using rigid registration.
5. Cache registered images to avoid repeated registration.
6. Select axial slices with high ROI coverage.
7. Normalize slices using z-score normalization.
8. Train 2D CNN and aggregate predictions at subject level.
9. Report bootstrap confidence interval for subject-level AUC.

---

## Ablation Branch

Ablation experiments test whether model components contribute to performance and whether the model may rely on shortcuts.

Tested factors:

| Factor | Full setting | Ablated setting |
|---|---|---|
| Slice selection | ROI-guided | whole-brain or random slices |
| Registration | MNI rigid registration | raw subject space |
| Normalization | z-score slice normalization | no normalization |
| Aggregation | mean probability | max probability |

Interpretation examples:

- If removing ROI does not reduce AUC, the anatomical prior may not be driving performance.
- If removing normalization increases AUC, the model may be exploiting scanner/site intensity style.
- If random slices perform similarly to ROI slices, the model may not depend on the hypothesized ADHD circuitry.

---

## Site Bias and Confound Baselines

Multi-site ADHD datasets can contain strong site-label correlations. To evaluate this, the project includes baseline models using non-image variables:

- site-only
- age + sex
- site + age + sex

These baselines are important because an image model must outperform simple confound baselines before it can be interpreted as learning disease-relevant information.

---

## fMRI Functional Connectivity Branch

### Step 1: fMRI manifest construction

The fMRI branch scans BIDS folders for resting-state `bold.nii.gz` files, keeps `ses-1`, deduplicates subjects, and merges labels from `participants.tsv` or phenotypic CSV files.

### Step 2: ROI time series extraction

The current prototype uses the Harvard-Oxford cortical atlas.

For each subject:

1. Extract ROI-wise time series using `NiftiLabelsMasker`.
2. Standardize and detrend time series.
3. Compute ROI × ROI correlation matrix.

### Step 3: Graph construction

Each subject is represented as a graph:

- Node = ROI
- Edge = functional connectivity between ROI pairs
- Node feature = ROI-level time-series summary or connectivity-derived feature
- Label = ADHD/control

Key rule:

> All subjects must use the same ROI node set and node order.

Dynamic deletion of missing or low-signal ROIs is avoided because it creates inconsistent graph dimensions and causes sample loss. Missing/invalid values are replaced with zero when appropriate.

### Step 4: GNN classifier

The current prototype uses a simple GCN:

- GCNConv
- ReLU
- dropout
- global mean pooling
- linear classifier

Evaluation uses subject-level train/test splits and AUC.
