# Reproduce the multimodal v2 analysis

This package reproduces the frozen 2026-09-10 multimodal analysis and runs an explicitly post hoc statistical/sensitivity audit. It does not alter the historical run. It is separate from the earlier n=409 BrainLM benchmark and from the portfolio branch.

## Reproduction boundaries

1. **Statistical recomputation:** regenerate original CV/LOSO contrast tables, calibration tables, the original decision and three original figures from saved held-out predictions.
2. **Sensitivity analysis:** matched subjects and fixed site weights; exact descriptive decomposition; symmetric final-alpha decomposition; validation-only final-selector bootstrap.
3. **Fresh model fitting:** recompute all 378 within-subject covariances from frozen A424 time series; for each of 45 CV and 21 LOSO units, reconstruct training-only geometry, features and confounds, train the LR/MLP models from scratch with original seeds, reselect validation-only fusion weights, and compare all 17 outputs for validation and test against the original run.

Level 3 is independent execution of hash-identical training code in a fresh environment, not an independently authored algorithm. It starts from the frozen time-series and regional-volume derivatives. Raw MRI preprocessing, a new segmentation run, independent anatomical QC, external validation, and new-site generalization are **not** claimed.

## Source and third-party provenance

`legacy/` contains the transitive local source closure needed to import and run v2, including the seven modules missing from the earlier public snapshot. Despite its historical name, it is an active dependency of the maintained runner, not an alternate project version. The nine protocol-listed source files match their frozen SHA256 values. `legacy_manifest.json` covers all packaged files. The runner explicitly supplies separate input/output locations and invokes only the needed functions. The inventory helper now takes user-supplied directories; its package hash changed, while the nine protocol-listed sources and the imported `norm_id`/`digest` implementations remain unchanged. See [portable paths and snapshot compatibility](../docs/PORTABLE_PATHS.md) before resuming or verifying a historical run.

The original patched Nilearn 0.12.1, NiBabel 5.3.2 and Packaging 25.0 sources are under `legacy/vendor/connectome0121/`. Tests and bytecode are excluded. Their original license notices are retained under the corresponding `.dist-info/licenses/` directories. These third-party licenses apply separately from the project's MIT license. Vendoring preserves the exact geometry implementation rather than substituting an unverified upstream version.

## Private inputs

Obtain ADHD-200 data according to the original access terms. The published repository does not distribute subject-level files. `--source` must identify an authorized private analysis workspace containing:

- `runs/structural_qc_locked_20260909/qc_lock.json`
- `runs/structural_features378_20260909/volumes_NOT_TRAINING_READY.npz`
- `runs/demographic_increment_20260908_locked_v2/{cohort,splits}.csv`
- `runs/temporal_cache_20260907_113751/{timeseries.npz,verification.json}`
- `runs/structural_fusion_v2_20260910/`, including frozen protocol, covariance reference, cohort/split records, every original unit's completion manifest/predictions, and original summaries/statistics.

The historical volume filename does not constitute a new readiness decision; eligibility is governed by the frozen QC lock. The runner checks the frozen input hashes, raw time-series hash, source hashes, all 66 original completion manifests and exact subject-role identities before training. The post hoc `reference_manifest.json` also binds 910 reference CSV/JSON files, including all 12 derived cohort/split files used for fitting. This snapshot is provenance evidence, not prospective registration. Published aggregate tables alone cannot support full refitting.

## Environment

Training used CPython 3.12.14 and the exact CPU dependencies in `requirements-runtime.lock`. The vendored packages are resolved by the preserved source import path. Example setup with uv:

```bash
uv venv --python 3.12 .venv-reproduce
uv pip install --python .venv-reproduce/bin/python \
  --extra-index-url https://download.pytorch.org/whl/cpu \
  --index-strategy unsafe-best-match -r reproduction/requirements-runtime.lock
```

Only the explicitly named PyPI and official PyTorch CPU indexes are intended here; the option permits uv to resolve the pinned packages across them. On the verified server the same setup succeeded offline from its existing cache. A clean local statistics environment used CPython 3.14.4 and `requirements-statistics.lock`; its five original tables and decision reproduced exactly.

## Commands

Set `SOURCE` to the private original workspace and `DEST` to a **new, separate** run directory. Never point `DEST` into the original run.

```bash
.venv-reproduce/bin/python reproduction/reproduce_v2.py \
  --source "$SOURCE" --out "$DEST" --workers 1 --limit 1
# Check reproduction_report.json: first unit must complete and match.
.venv-reproduce/bin/python reproduction/reproduce_v2.py \
  --source "$SOURCE" --out "$DEST" --workers 6
```

The second command validates and reuses the completed reproduction unit; it does not retrain it. The full run plans exactly 66 units. Each worker uses four training/BLAS threads. Six workers are intended only for a host with sufficient CPU and RAM; use fewer otherwise. Incomplete units are not silently overwritten. Source/environment changes invalidate resumption. Detach a long SSH job with `setsid nohup` and retain its logs; do not start a second supervisor against the same output.

Fresh predictions are compared on exact subject/model keys, including labels/sites, with `rtol=1e-5, atol=1e-6`; selected final fusion weights must also agree. Outputs distinguish `complete_matched`, `complete_with_differences`, and failure. Completion of one trial unit is not completion of 66. Check `all_units_completed`, not merely a process exit. Per-unit resume additionally requires the last-written `reproduction_complete.json` marker, exact job identity and protocol hash. Summaries must succeed before the reviewed driver publishes terminal completion.

For saved-prediction analyses, set `RUN=$SOURCE/runs/structural_fusion_v2_20260910`. Each output path below must be new:

```bash
python reproduction/regenerate_tables.py --run "$RUN" --out "$STATS_OUT"
python reproduction/statistics_audit.py --run "$RUN" --out "$AUDIT_OUT"
python reproduction/fusion_sensitivity.py --run "$RUN" --out "$FUSION_OUT"
python reproduction/selector_stability.py --run "$RUN" --out "$SELECTOR_OUT"
python reproduction/paper_figures.py --tables "$AUDIT_OUT" --out "$FIGURE_OUT"
python -m pytest reproduction/tests -q
```

After fitting exits, run the independent final gate:

```bash
python reproduction/verify_fresh.py --source "$SOURCE" --out "$DEST" \
  --stats-out "$FRESH_STATS_OUT"
```

`FRESH_STATS_OUT` must be a new directory outside the original source workspace. This validates all 66 unit artifacts and exact roles, prediction/selection comparisons, six cohort summaries and their prediction concatenations, then calls `regenerate_tables.py --run "$DEST" --reference-run "$RUN" --out "$FRESH_STATS_OUT"`. It publishes `verified_reproduction.json` only after the five statistical/calibration tables, decision and three figures succeed. Failed final re-verification invalidates old success. The reference is read from the original run; no reference predictions or checkpoints are copied into fresh unit directories.

## Evidence and interpretation

- [Statistical interpretation audit](../docs/paper/STATISTICAL_INTERPRETATION.md)
- [Aggregate analysis tables](../results/paper_readiness_20260911/)
- [Publication figures](../figures/paper_readiness_20260911/)
- `recomputation_verification.json`: five original tables and original decision verification.
- `reproduction_manifest.json`, `covariance_comparison.json`, per-unit `comparison.json`, and final `reproduction_report.json`: fresh-fit evidence in the separate private output. A summarized, non-subject-level report is exported after completion.

Subject-level predictions, models and arrays remain private. Only aggregate evidence is eligible for a publication commit. See the repository ignore rules; do not use `git add -A` on the private analysis workspace.

## September 11 execution and review

The first unit was launched before the independent safeguard review. Its exact driver is preserved in `execution_history/reproduce_v2_launched_20260911.py`; the active server source was not silently changed. The reviewed driver in the package has stronger input/resume/completion gates and therefore a different SHA256. Do not replace an active driver or bypass its resume manifest check. The existing execution is accepted only through the separate `verify_fresh.py` final gate, which recognizes the preserved launch hash and independently verifies every unit.

`finish_execution.py` can wait for one explicitly identified existing training process, then run that gate. It never starts training. It waits for both PID start-time and command-line identity to disappear, so the launched driver's provisional terminal report cannot trigger verification before aggregation exits. A separate collection step copies aggregate proof/tables/figures back only after the server pipeline verifies successfully. Both steps fail explicitly; no verification result is inferred from a live PID.

The initial trial recomputed covariance from time series with a byte-identical result. Resuming the full execution reused that new covariance cache; the old driver's `recomputed_from_timeseries` field does not mean it recomputed on every invocation. The final gate verifies the raw time-series checksum and covariance provenance again.

The independent statistical review found no actionable computation errors. Reproduction review findings were addressed with tests for stale success, protected output paths, copied-fold resumption and transactional markers. **19 local tests passed**; the clean server audit environment also reproduced the original tables/decision/figures. See [live execution status](../docs/paper/FRESH_REPRODUCTION_STATUS.md) for what has actually completed.
