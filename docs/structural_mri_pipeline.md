# Structural MRI Pipeline

## Goal

Evaluate whether T1-weighted structural MRI contains subject-level signal for ADHD classification.

## Pipeline

```text
ADHD-200 BIDS T1 MRI
  → participants.tsv label extraction
  → anatomical QC filtering
  → subject-level deduplication
  → subject-level split
  → slice extraction
  → CNN training
  → subject-level aggregation
  → AUC / threshold analysis
```

## Baselines

### Single-slice baseline

Each subject contributes one middle axial slice. This validates the data pipeline and gives a conservative lower-bound baseline.

### Multi-slice baseline

Each subject contributes K slices from the central z-range. This tests whether more anatomical context improves performance.

### ROI-guided baseline

Each subject is registered to MNI152 2mm. Harvard-Oxford atlas masks define ADHD-relevant slices. The model then trains on ROI-heavy slices.

## Key Evaluation Rule

Never split slices randomly across train and test. Split subjects first, then extract slices.
