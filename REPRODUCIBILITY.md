# Reproducibility Guide

The supported reproduction path is code-based and tested. Exploratory notebooks have been removed from the final branch; Git history retains them for provenance.

## Supported execution paths

For a public, aggregate-only check that does not require ADHD-200 data:

```bash
make quickstart
make validate-public
make test
```

For the complete multimodal v2 workflow, use [the reproduction package](reproduction/README.md). It distinguishes statistical recomputation, sensitivity analysis, and fresh model fitting. Saved-prediction recomputation is not model retraining.

The final table and figure package is assembled by the scripts in [`reporting/`](reporting/) and bound by [`PACKAGE_MANIFEST.json`](results/tables_figures_20260914/PACKAGE_MANIFEST.json).

## Private inputs

Authorized ADHD-200 derivatives, large arrays, subject-level predictions, and model checkpoints stay outside the repository. Exact private inputs and output isolation requirements are documented in [`reproduction/README.md`](reproduction/README.md).

The directory `reproduction/legacy/` is retained because the current fresh-fit runner imports and hash-verifies that frozen source closure. `reproduction/execution_history/` is retained because the final verifier recognizes the exact driver used by the completed server run. Both are active provenance dependencies of the maintained reproduction path.

## Leakage controls

- one subject appears in only one evaluation partition
- test sites are never used for fitting preprocessing
- feature scaling is fit on training data
- feature selection is fit on training data
- confound residualization is fit on training data
- hyperparameters are selected inside training sites
- held-out site predictions are saved once per outer fold

## Primary metric

The primary within-dataset metric is mean AUC across 20 outer folds from repeated site-and-label-stratified CV. For the unseen-site stress test, macro AUC is the unweighted mean of valid held-out-site AUC values. These metrics answer different questions and must not be substituted for each other.

## Randomness and environments

The maintained analysis uses fixed seeds where supported and pinned environments in `reproduction/requirements-statistics.lock` and `reproduction/requirements-runtime.lock`. Fresh outputs are checked against the frozen reference with explicit numerical tolerances; aggregate statistics and artifact hashes are verified separately.

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

The accepted 66-unit replay checks all model outputs, validation-selected fusion weights, summaries, statistical tables, the decision, and figures against the frozen reference. This establishes computational reproducibility for the specified pipeline. It does not establish external validity, clinical utility, or a general absence of imaging signal.
