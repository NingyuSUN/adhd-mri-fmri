# Engineering guide

This repository has two deliberately separate execution paths.

## Five-minute portfolio path

The aggregate-only path is safe to run after cloning and does not require ADHD-200 data:

```bash
python tools/portfolio_quickstart.py --output-dir artifacts/portfolio_quickstart
cat artifacts/portfolio_quickstart/summary.md
python tools/validate_public_artifacts.py
```

It reads the committed primary model and contrast tables, checks their schema, and writes a deterministic JSON/Markdown report. This path demonstrates the reporting contract and CI checks; it does not train or select a model.

## Full research path

The feature-level replay is a separate, gated workflow in [`reproduction/README.md`](../reproduction/README.md). It requires authorized private ADHD-200 derivatives and a new output directory. The public repository contains aggregate evidence and the frozen source closure, but not raw MRI, subject-level predictions, checkpoints, credentials, or private server paths.

## Data contracts

- A participant is the split unit; slices and time windows never cross partitions.
- Aggregate tables may contain cohort, site, label counts, metrics, intervals, and calibration summaries.
- Public CSVs must not contain `subject_id`, `participant_id`, raw paths, individual predictions, or scores.
- `results/tables_figures_20260914/PACKAGE_MANIFEST.json` binds the public table/figure package by SHA-256 and byte count.
- The three QC cohorts overlap; their rows are not independent replications.

## Verification layers

1. `pytest reproduction/tests -q` checks statistical and identity invariants.
2. `python tools/portfolio_quickstart.py --check` checks the recruiter-safe aggregate path.
3. `python tools/validate_public_artifacts.py` checks manifest hashes, counts, headers, and path redaction.
4. The independent 66-unit replay acceptance is recorded in [`docs/paper/FRESH_REPRODUCTION_STATUS.md`](paper/FRESH_REPRODUCTION_STATUS.md).

Passing these checks proves engineering and reproducibility properties. It does not prove external validity, expert anatomical QC, causal interpretation, clinical utility, or a deployable diagnostic model.

## Failure modes and recovery

- Missing aggregate files or changed columns: stop at the quickstart schema check and inspect the package manifest.
- Manifest hash mismatch: regenerate the package from reviewed source outputs; do not silently overwrite a frozen result.
- Full replay failure: leave the fresh output directory for diagnosis and rerun the independent gate only after the source/environment/job identity is verified.
- Private-data access failure: use the aggregate-only path; do not copy raw files into the repository.

## Five-minute reviewer route

1. Read the top-level README and [`PORTFOLIO_CASE_STUDY.md`](../PORTFOLIO_CASE_STUDY.md).
2. Run the aggregate-only quickstart.
3. Inspect [`results/tables_figures_20260914/index.html`](../results/tables_figures_20260914/index.html).
4. Read [`docs/paper/STATISTICAL_INTERPRETATION.md`](paper/STATISTICAL_INTERPRETATION.md) and [`docs/paper/FRESH_REPRODUCTION_STATUS.md`](paper/FRESH_REPRODUCTION_STATUS.md).
5. Use the CI workflow and `Makefile` as the reproducible commands for future changes.
