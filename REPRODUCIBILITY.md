# Reproducibility Guide

## Random Seeds

The scripts use seed 42 where possible:

```python
SEED = 42
np.random.seed(SEED)
tf.random.set_seed(SEED)
```

For PyTorch-based GNN experiments, also set:

```python
import torch

torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)
```

## Recommended Execution Order

```text
01_t1_single_slice_baseline_colab.py
02_t1_multislice_baseline_and_leakage_demo_colab.py
03_t1_roi_guided_cnn_colab.py
04_t1_ablation_site_bias_colab.py
05_fmri_connectivity_gnn_colab.py
```

## Google Colab Notes

The original analysis was developed primarily in Google Colab with Google Drive mounted at:

```text
/content/drive/MyDrive/
```

If running locally, update all absolute paths.

## PyTorch Geometric Installation

PyTorch Geometric wheels depend on the installed PyTorch and CUDA versions. In Colab, use a version-aware install pattern:

```python
import torch

torch_version = torch.__version__.split('+')[0]
if torch.cuda.is_available():
    cuda_version = 'cu' + torch.version.cuda.replace('.', '')
    pyg_url = f'https://data.pyg.org/whl/torch-{torch_version}+{cuda_version}.html'
else:
    pyg_url = f'https://data.pyg.org/whl/torch-{torch_version}.html'

!pip install torch-scatter torch-sparse torch-cluster torch-spline-conv torch-geometric -f {pyg_url}
```

## Caching

Registration is slow. The ROI-guided T1 pipeline caches MNI-registered images. Recommended cache directory:

```text
/content/drive/MyDrive/ADHD200-cache/mni2mm_rigid/
```

Do not commit cache files to GitHub.

## Result Saving

Recommended output files:

```text
results/
├── t1_single_slice_summary.csv
├── t1_multislice_summary.csv
├── t1_roi_guided_summary.csv
├── t1_ablation_results.csv
├── site_bias_baselines.csv
├── fmri_gnn_summary.csv
└── foldwise_metrics.csv
```

## Minimum Reproducibility Checklist

- [ ] Raw data source documented.
- [ ] Manifest CSV saved.
- [ ] Exact split strategy documented.
- [ ] Subject-level deduplication performed.
- [ ] Random seed fixed.
- [ ] Model hyperparameters documented.
- [ ] Fold-wise metrics saved.
- [ ] Bootstrap CI reported.
- [ ] Site-bias baseline reported.
