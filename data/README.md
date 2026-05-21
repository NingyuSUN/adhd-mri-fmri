# Data

This directory is intentionally empty. The ADHD-200 dataset is publicly available but must be downloaded separately due to its large size (~200 GB).

## Download Instructions

### Option 1: AWS CLI (recommended)

```bash
pip install awscli

aws s3 sync s3://fcp-indi/data/Projects/ADHD200/RawDataBIDS/ \
  /your/local/path/RawDataBIDS \
  --no-sign-request
```

### Option 2: Individual site downloads

The following sites are used in this project:

| Site | S3 path |
|------|---------|
| Peking_1 | `s3://fcp-indi/.../RawDataBIDS/Peking_1/` |
| NYU | `s3://fcp-indi/.../RawDataBIDS/NYU/` |
| KKI | `s3://fcp-indi/.../RawDataBIDS/KKI/` |
| OHSU | `s3://fcp-indi/.../RawDataBIDS/OHSU/` |
| Pittsburgh | `s3://fcp-indi/.../RawDataBIDS/Pittsburgh/` |
| WashU | `s3://fcp-indi/.../RawDataBIDS/WashU/` |

Phenotypic CSVs are also on S3: `Peking_1_phenotypic.csv`, `NYU_phenotypic.csv`, etc.

## Expected BIDS Structure

```
RawDataBIDS/
└── Peking_1/
    ├── participants.tsv         ← subject labels + QC
    ├── sub-0010001/
    │   └── ses-1/
    │       ├── anat/
    │       │   └── sub-0010001_ses-1_T1w.nii.gz
    │       └── func/
    │           └── sub-0010001_ses-1_task-rest_bold.nii.gz
    └── ...
```

## Generated Files (by notebooks)

After running the notebooks, the following manifest files are created:

| File | Pipeline | Description |
|------|----------|-------------|
| `manifest_all_sitefirst_strictpass_noBrown.csv` | T1w | Multi-site T1w manifest with QC-pass subjects |
| `fmri_manifest.csv` | fMRI | Multi-site fMRI manifest with matched labels |
