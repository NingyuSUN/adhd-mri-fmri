# Data Documentation

## Data license

This repository's code is MIT-licensed (see [`LICENSE`](LICENSE)). **The MIT license covers
the code only.** ADHD-200 MRI/fMRI data, phenotypic labels, and derivatives remain subject to
their own original data-use terms from the contributing sites and the ADHD-200 Global
Competition/consortium, independent of this repository's license.

## Dataset

This project uses ADHD-200 MRI/fMRI data. Raw neuroimaging files are not included in this repository.

## Expected Directory Layout

Choose a local or mounted data directory and pass it to the relevant command.
The layout below is relative to that directory; no specific drive is required:

```text
ADHD200-data/
├── RawDataBIDS/
│   ├── Peking_1/
│   │   ├── participants.tsv
│   │   └── sub-*/ses-1/anat/*_T1w.nii.gz
│   ├── NYU/
│   │   ├── participants.tsv
│   │   └── sub-*/ses-1/func/*rest*bold.nii.gz
│   └── ...
├── manifest_all_sitefirst_strictpass_noBrown.csv
└── fmri/
    └── fmri_manifest.csv
```

## Structural MRI Manifest

Expected file:

```text
manifest_all_sitefirst_strictpass_noBrown.csv
```

Recommended columns:

| Column | Meaning |
|---|---|
| `sub_id` | Subject identifier normalized to BIDS-style `sub-*` |
| `site` | Acquisition site |
| `t1_path` | Path to T1-weighted MRI file |
| `y` | Binary label: 0 = control, 1 = ADHD |
| `sex` | Sex/gender metadata if available |
| `age` | Age metadata if available |

## fMRI Manifest

Expected file:

```text
fmri_manifest.csv
```

Recommended columns:

| Column | Meaning |
|---|---|
| `site` | Acquisition site |
| `subject_id` | Subject identifier |
| `fmri_path` | Path to resting-state fMRI file |
| `final_label` | Binary label: 0 = control, 1 = ADHD |

## Label Construction

Labels are read from site-level `participants.tsv` or recovered from ADHD-200 phenotypic CSV files when needed.

General mapping:

| Raw diagnosis | Binary label |
|---|---:|
| Typically Developing / Control / TDC / 0 | 0 |
| ADHD / ADHD subtype / 1 / 2 / 3 | 1 |

## Quality Control

Structural MRI analyses use anatomical QC where available. Recommended strict pass values:

- `Pass`
- `1`
- `true` / `yes` if encoded as boolean-like fields

Sites or subjects without reliable QC should be documented separately.

## Data Exclusion Notes

The current structural manifest excludes Brown in the strict-pass multi-site setup because of metadata/QC harmonization issues in the working version. This should be revisited before final publication-level analysis.
