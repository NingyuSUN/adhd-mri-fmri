# ADHD Classification from Brain MRI using Deep Learning

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](#)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-orange)](#)
[![PyTorch Geometric](https://img.shields.io/badge/PyG-GNN-red)](#)
[![Status](https://img.shields.io/badge/status-active%20research-yellow)](#)

This repository investigates whether structural MRI and resting-state fMRI contain reproducible signal for classifying ADHD versus typically developing controls using the ADHD-200 multi-site dataset.

The project is organized as a research pipeline rather than a single model demonstration. It starts from conservative structural MRI baselines, moves to ROI-guided modeling, then tests confounding and shortcut learning through ablation and site-bias analyses. The current fMRI branch represents the brain as a functional connectivity graph and evaluates graph neural network models.

> **Important note**  
> This repository does **not** claim a clinically deployable ADHD diagnostic model. The central research question is whether image-derived signals generalize beyond site, scanner, demographic, and preprocessing confounds.

---

## Research Questions

1. Can T1-weighted structural MRI alone provide stable subject-level discrimination between ADHD and controls?
2. Does ROI-guided slice selection improve signal compared with single-slice or generic multi-slice baselines?
3. Are apparent MRI classification signals robust to ablation, subject-level splitting, bootstrap uncertainty, and site-bias controls?
4. Does resting-state fMRI functional connectivity provide a stronger modeling target than structural MRI?
5. Can graph neural networks model brain connectivity while preserving a fixed and reproducible ROI graph representation?

---

## Repository Structure

```text
adhd-mri-fmri/
├── README.md
├── PROJECT_STATUS.md
├── DATA.md
├── METHODS.md
├── RESULTS.md
├── LIMITATIONS.md
├── REPRODUCIBILITY.md
├── ROADMAP.md
├── requirements.txt
├── requirements-colab.txt
├── environment.yml
├── .gitignore
├── CITATION.cff
├── LICENSE
├── data/
│   └── README.md
├── docs/
│   ├── structural_mri_pipeline.md
│   ├── fmri_gnn_pipeline.md
│   ├── ablation_and_site_bias.md
│   ├── model_evaluation.md
│   └── github_about.md
├── figures/
│   └── README.md
├── notebooks/
│   ├── 01_t1_single_slice_baseline_colab.py
│   ├── 02_t1_multislice_baseline_and_leakage_demo_colab.py
│   ├── 03_t1_roi_guided_cnn_colab.py
│   ├── 04_t1_ablation_site_bias_colab.py
│   └── 05_fmri_connectivity_gnn_colab.py
├── results/
│   ├── README.md
│   └── result_table_template.csv
└── src/
    └── README.md
```

The files in `notebooks/` are Colab-exported Python scripts. They can be uploaded back to Google Colab or converted to `.ipynb` if notebook-style presentation is preferred.

---

## Dataset

The project uses ADHD-200 neuroimaging data in BIDS-like format.

Main modalities:

- **T1-weighted structural MRI** for anatomical/structural modeling
- **Resting-state fMRI** for functional connectivity modeling

Main metadata sources:

- `participants.tsv` inside each site folder
- additional ADHD-200 phenotypic CSV files when site-level labels require recovery

Raw MRI/fMRI files are not included in this repository due to dataset size and data-access constraints. See [`DATA.md`](DATA.md) for the expected directory layout and manifest format.

---

## Method Overview

### 1. Structural MRI baselines

The T1 branch follows a progressive baseline design:

```text
participants.tsv
      ↓
subject_id ↔ ADHD/control label
      ↓
BIDS T1 path collection
      ↓
QC filtering + subject-level deduplication
      ↓
single-slice / multi-slice extraction
      ↓
2D CNN
      ↓
subject-level prediction + AUC/threshold analysis
```

The single-slice and multi-slice baselines test whether simple structural slices contain stable ADHD signal before adding more complex preprocessing.

### 2. ROI-guided structural MRI CNN

The ROI-guided model introduces neuroanatomical priors:

```text
T1 MRI
  → rigid registration to MNI152 2mm
  → Harvard-Oxford atlas
  → ADHD-relevant ROI mask
  → ROI-heavy axial slice selection
  → 2D CNN
  → mean aggregation across slices
  → subject-level AUC + bootstrap CI
```

ROI selection focuses on frontal cortex, cingulate regions, striatum, thalamus, pallidum, and accumbens-related circuitry.

### 3. Ablation and site-bias analysis

The ablation branch tests whether model performance depends on the intended components:

- ROI-guided slices vs whole-brain or random slices
- registration on/off
- slice normalization on/off
- mean vs max subject aggregation
- site-only and demographic baselines
- fold-wise consistency and out-of-fold AUC

This branch is designed to detect shortcut learning, especially scanner/site-driven prediction.

### 4. fMRI functional connectivity GNN

The fMRI branch represents each subject as a brain connectivity graph:

```text
resting-state fMRI
  → Harvard-Oxford ROI time series
  → ROI × ROI correlation matrix
  → graph construction
  → fixed node set / zero padding when needed
  → GCN classifier
  → subject-level AUC
```

A key design decision is to keep a fixed ROI set across subjects. Dynamic ROI deletion can lead to inconsistent graph dimensions and severe sample loss.

---

## Key Design Principles

### Subject-level splitting

All valid evaluations split data by subject, not by slice. A subject must appear in only one of train, validation, or test.

### Subject-level metrics

Slice-level predictions are intermediate outputs. Final reporting should aggregate predictions to the subject level.

### AUC over accuracy

Accuracy is unstable and often misleading in small, imbalanced medical datasets. AUC and threshold-based metrics such as recall, precision, confusion matrix, and R90-style operating points are more informative.

### Confound-aware interpretation

Multi-site MRI datasets often contain strong site/scanner structure. A model that performs well may still be learning site identity, intensity style, or demographic imbalance rather than ADHD-related neurobiology.

---

## Current Findings

The project has reached the following stage:

- T1 single-slice CNN baseline is implemented.
- T1 multi-slice CNN with subject-level aggregation is implemented.
- A leakage demonstration shows why slice-level random splitting is invalid.
- ROI-guided T1 CNN using MNI registration and Harvard-Oxford atlas is implemented.
- Ablation experiments are implemented for ROI, registration, normalization, and aggregation.
- Site-bias analysis suggests that site information alone can carry substantial predictive signal.
- fMRI connectivity graph construction and GCN training are implemented, with a focus on fixed ROI representation.

See [`RESULTS.md`](RESULTS.md) for the current result summary and recommended reporting format.

---

## Quick Start

### 1. Clone repository

```bash
git clone https://github.com/NingyuSUN/adhd-mri-fmri.git
cd adhd-mri-fmri
```

### 2. Install dependencies

For general Python environments:

```bash
pip install -r requirements.txt
```

For Google Colab, use:

```bash
pip install -r requirements-colab.txt
```

PyTorch Geometric may require installation from the official wheel index matching the current PyTorch and CUDA version. See [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md).

### 3. Prepare data

Expected raw data root:

```text
/content/drive/MyDrive/ADHD200-data/RawDataBIDS/
```

Expected structural manifest:

```text
/content/drive/MyDrive/ADHD200-data/manifest_all_sitefirst_strictpass_noBrown.csv
```

Expected fMRI manifest:

```text
/content/drive/MyDrive/ADHD200-data/fmri/fmri_manifest.csv
```

### 4. Run analyses

Recommended order:

```text
01_t1_single_slice_baseline_colab.py
02_t1_multislice_baseline_and_leakage_demo_colab.py
03_t1_roi_guided_cnn_colab.py
04_t1_ablation_site_bias_colab.py
05_fmri_connectivity_gnn_colab.py
```

---

## Recommended GitHub About

**Description**

```text
ADHD-200 MRI/fMRI classification using ROI-guided CNNs, functional connectivity GNNs, ablation studies, and site-bias analysis.
```

**Topics**

```text
adhd, mri, fmri, neuroimaging, deep-learning, graph-neural-network, medical-ai, adhd200, nilearn, tensorflow, pytorch-geometric
```

---

## Author

**Ningyu Sun**

Research interests: neuroimaging, medical AI, genomics, machine learning, and interpretable biomedical modeling.

---

## License

This repository is released under the MIT License. Dataset access and usage remain subject to the original ADHD-200 data terms.
