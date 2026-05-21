# fMRI Functional Connectivity GNN Pipeline

## Goal

Model ADHD-related differences in functional brain networks using resting-state fMRI.

## Pipeline

```text
Resting-state fMRI
  → ROI time-series extraction
  → functional connectivity matrix
  → graph construction
  → graph neural network
  → subject-level prediction
```

## ROI Time Series

The current prototype uses Harvard-Oxford cortical atlas ROIs. Each ROI provides a time series representing average activity across time.

## Functional Connectivity

Connectivity is estimated using Pearson correlation between ROI time series.

## Graph Representation

- Nodes: ROIs
- Edges: functional connectivity values
- Node features: ROI-level summaries or connectivity-derived features
- Graph label: ADHD/control

## Critical Issue

All subjects must share the same node set and node order. If ROIs are dynamically removed, graph dimensions become inconsistent and many subjects are lost.

Recommended handling:

- fixed atlas ROI list
- no per-subject ROI deletion
- NaN/invalid values converted to zero
- explicit logging of ROI counts
