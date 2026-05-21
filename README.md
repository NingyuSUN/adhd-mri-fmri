# ADHD Classification from Brain MRI using Deep Learning

A research project applying deep learning to classify ADHD vs. typically developing controls using the **ADHD-200 multi-site dataset**. The project covers two complementary pipelines:

1. **ROI-guided Structural MRI (T1w)** — 2D CNN on atlas-selected brain slices  
2. **Functional MRI (rs-fMRI)** — Graph Neural Network (GNN/GAT) on functional connectivity graphs

---

## Table of Contents

- [Project Overview](#project-overview)
- [Dataset](#dataset)
- [Pipeline 1: Structural MRI (T1w CNN)](#pipeline-1-structural-mri-t1w-cnn)
- [Pipeline 2: Functional MRI (GNN)](#pipeline-2-functional-mri-gnn)
- [Key Results](#key-results)
- [Error Analysis & Ablation](#error-analysis--ablation)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Limitations & Future Work](#limitations--future-work)

---

## Project Overview

ADHD is a neurodevelopmental disorder with subtle and heterogeneous brain signatures. This project investigates whether machine learning can reliably detect these signatures from neuroimaging data across multiple acquisition sites.

**Key design choices:**
- **Subject-level train/test splits** — prevents data leakage across all experiments
- **Atlas-guided ROI selection** (Harvard-Oxford) — focuses models on ADHD-relevant circuits (PFC, cingulate, striatum, thalamus)
- **Multi-site generalization** — data from 7–8 sites to probe cross-scanner robustness
- **Bootstrap confidence intervals** — honest uncertainty quantification on small test sets

---

## Dataset

**ADHD-200** — publicly available multi-site neuroimaging dataset  
Source: [fcon_1000.projects.nitrc.org](http://fcon_1000.projects.nitrc.org/indi/adhd200/)  
S3 mirror: `s3://fcp-indi/data/Projects/ADHD200/RawDataBIDS/`

| Site | Modality | Approx. N (QC pass) |
|------|----------|---------------------|
| Peking_1 | T1w + fMRI | ~130 |
| NYU | T1w + fMRI | ~216 |
| KKI | T1w + fMRI | ~80 |
| OHSU | T1w + fMRI | ~70 |
| Pittsburgh | T1w + fMRI | ~50 |
| WashU | T1w | ~60 |
| Brown | excluded (QC) | — |

**Labels:** `0` = Typically Developing Control, `1` = ADHD (any subtype)  
**QC filter:** `qc_anatomical_1 == "pass"` (T1w pipeline); `ses-1` rs-fMRI scans only

---

## Pipeline 1: Structural MRI (T1w CNN)

### Approach

```
Raw T1w NIfTI
    │
    ▼
Rigid registration → MNI152 2mm (ANTsPy, cached)
    │
    ▼
ROI mask (Harvard-Oxford: PFC + cingulate + subcortical)
    │
    ▼
Select K=16 ROI-dense z-slices
    │
    ▼
Per-slice z-score normalization + resize to 128×128
    │
    ▼
2D CNN  →  slice-level probability
    │
    ▼
Mean-aggregate per subject  →  subject AUC
```

### Model Architecture

```
Input (128×128×1)
→ Conv2D(16) + MaxPool
→ Conv2D(32) + MaxPool
→ Conv2D(64) + GlobalAvgPool
→ Dropout(0.2)
→ Dense(1, sigmoid)
```

### Cross-validation

- **5-fold stratified CV** (subject-level, no slice leakage)
- Early stopping on `val_loss` (patience=2)
- Bootstrap 95% CI on OOF AUC (n=2000)

---

## Pipeline 2: Functional MRI (GNN)

### Approach

```
rs-fMRI NIfTI (ses-1)
    │
    ▼
NiftiLabelsMasker (Harvard-Oxford cortical, 48 ROIs)
    │
    ▼
Time series (T × 48), standardized + detrended
    │
    ▼
Pearson correlation matrix (48 × 48)  ← node features
    │
    ▼
Threshold |r| > 0.3  →  edges
    │
    ▼
PyG graph: nodes=48 ROIs, edges=FC, x=FC row vector
    │
    ▼
GAT (Graph Attention Network)  →  subject-level AUC
```

### Model Progression

| Version | Architecture | Data | Best AUC |
|---------|-------------|------|----------|
| GCN_v1 | GCN, scalar node feat | NYU (32) | ~0.50 (collapsed) |
| GCN_v2 | GCN, FC-row features | NYU (216) | ~0.63 |
| GAT_v1 | 2-layer GAT, heads=4 | All sites (794) | **~0.64** |
| GAT_v2 | GAT, hidden=128 | All sites (794) | ~0.62 (overfit) |

**GAT_v1** is the recommended model: best generalization on multi-site data.

```python
class GAT_v1(torch.nn.Module):
    def __init__(self, in_channels=48, hidden_channels=64, heads=4):
        ...
        self.conv1 = GATConv(in_channels, hidden_channels, heads=heads)
        self.conv2 = GATConv(hidden_channels * heads, hidden_channels, heads=1)
        self.fc    = Linear(hidden_channels, 2)
        self.dropout = Dropout(0.5)
```

---

## Key Results

### Structural MRI (T1w)
| Metric | Value |
|--------|-------|
| OOF subject AUC | ~0.71 |
| Bootstrap 95% CI | ±0.05 (approx.) |
| Sites | 7 (excl. Brown) |
| Subjects | ~900 |

### Functional MRI (fMRI / GAT)
| Site | AUC | N (test) |
|------|-----|----------|
| NYU | **0.796** | ~44 |
| Peking_1 | 0.697 | ~32 |
| OHSU | 0.681 | ~25 |
| Peking_2/3 | 0.43–0.44 | ~18 |
| KKI | 0.00* | ~17 |
| **All sites** | **0.64** | ~159 |

*KKI test set had severe class imbalance; AUC unreliable.

> **Interpretation:** Both pipelines achieve AUC in the 0.65–0.80 range on favorable sites, consistent with the neuroimaging literature on structural-only ADHD classification. Cross-site generalization remains the core challenge.

---

## Error Analysis & Ablation

### Error Analysis (T1w pipeline)

Subjects are categorized into TP / TN / FP / FN using the Youden-J optimal threshold. Key outputs:
- `subject_error_table.csv` — per-subject group + prediction probability
- `site_performance.csv` — AUC / accuracy / error rate per site
- `confident_FP.csv` / `confident_FN.csv` — high-confidence wrong predictions

**Finding:** FP/FN are concentrated in subjects near the decision boundary (predicted prob ≈ 0.5) rather than high-confidence errors, consistent with label uncertainty near diagnostic thresholds.

### Ablation Ideas

| Ablation | Question |
|----------|----------|
| Remove ROI mask | Do ROI-selected slices outperform whole-brain slices? |
| Cortical-only ROI | Does subcortical (caudate, putamen) information help? |
| Fewer z-slices (K=8 vs K=16) | How sensitive is AUC to slice count? |
| GCN vs GAT | Does attention improve over fixed-weight aggregation? |

---

## Installation

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/adhd-fmri-gnn.git
cd adhd-fmri-gnn

# Install Python dependencies
pip install -r requirements.txt
```

### Requirements

```
nilearn>=0.10
nibabel>=5.0
antspyx>=0.4
scikit-learn>=1.3
tensorflow>=2.12        # T1w CNN pipeline
torch>=2.0              # fMRI GNN pipeline
torch-geometric>=2.3
pandas>=2.0
numpy
matplotlib
seaborn
tqdm
```

---

## Usage

### Google Colab (recommended)

Both notebooks are designed to run end-to-end on Google Colab with Drive-mounted data.

1. Upload your ADHD-200 BIDS data to Google Drive
2. Open `notebooks/adhd_roi_guided.ipynb` or `notebooks/adhd_fmri.ipynb` in Colab
3. Edit the `BASE_DIR` / `MANIFEST_PATH` path variable at the top of the notebook
4. Run all cells

### Data Download

```bash
# Download ADHD-200 via AWS CLI (no credentials needed)
aws s3 sync s3://fcp-indi/data/Projects/ADHD200/RawDataBIDS/ \
  /your/local/path/RawDataBIDS \
  --no-sign-request
```

### Build the Multi-site Manifest (T1w)

```python
# Produces manifest_all_sitefirst_strictpass_noBrown.csv
# Contains: sub_id, site, t1_path, y, sex, age
# Run the manifest-building cells in adhd_roi_guided.ipynb
```

### Build the fMRI Manifest

```python
# Produces fmri_manifest.csv
# Contains: site, subject_id, fmri_path, final_label
# Run the fmri manifest cells in adhd_fmri.ipynb
```

---

## Project Structure

```
adhd-fmri-gnn/
│
├── README.md
├── requirements.txt
│
├── notebooks/
│   ├── adhd_roi_guided.ipynb   # T1w CNN pipeline (Google Colab)
│   └── adhd_fmri.ipynb         # fMRI GNN pipeline (Google Colab)
│
├── models/
│   ├── cnn_2d.py               # Small 2D CNN for T1w slices
│   └── gat.py                  # GAT_v1 and variant definitions
│
├── utils/
│   ├── registration.py         # ANTsPy rigid registration + caching
│   ├── roi.py                  # Harvard-Oxford atlas ROI mask helpers
│   ├── dataset.py              # Slice/graph dataset builders
│   ├── metrics.py              # Bootstrap AUC CI, subject aggregation
│   └── manifest.py             # Multi-site manifest builder
│
├── data/
│   └── README.md               # Data download instructions
│
└── results/
    └── README.md               # Expected output files description
```

---

## Limitations & Future Work

**Current limitations:**
- Small effective sample sizes per site → wide CIs, unstable AUC on some sites
- Registration caching is required for practical runtime (first run is slow)
- fMRI pipeline uses only cortical atlas (48 ROIs); subcortical ROIs not yet integrated
- No age/sex covariate correction
- Site effect analysis shows the model may partially learn scanner fingerprints

**Planned improvements:**
- [ ] Domain Adversarial Neural Network (DANN-GNN) for site-invariant features
- [ ] Leave-One-Site-Out (LOSO) cross-validation for proper generalization estimate
- [ ] Dynamic functional connectivity features (sliding-window FC)
- [ ] Combined T1w + fMRI multimodal model
- [ ] Attention weight visualization for circuit-level interpretability

---

## Citation

If you use this code, please cite the ADHD-200 consortium:

> ADHD-200 Consortium (2012). The ADHD-200 Consortium: A Model to Advance the Translational Potential of Neuroimaging in Clinical Neuroscience. *Frontiers in Systems Neuroscience*, 6, 62.

---

## License

MIT License — see `LICENSE` for details.
