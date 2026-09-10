# Reproducing the fMRI portfolio

The package distinguishes four levels. Passing one level does not imply the next.

| Level | Inputs | What it establishes | Current verification |
|---|---|---|---|
| Synthetic demo | Generated 120-subject toy data | Code execution, training/validation selection, checkpoint replay | Run locally |
| Frozen evidence replay | Private frozen release with manifest and prediction tables | File integrity, split/label alignment, AUC aggregation, validation weights and fusion arithmetic | All three runs passed |
| Real-data preparation | Audited cohort in original runtime layout | Original 378-person split generation and covariate setup through portable wrapper | Passed; no training |
| Complete scientific rerun | Time-series/feature caches, prerequisite metadata, recorded environment | Training through prediction and downstream controls | Wrapper supplied and inputs preflighted; full run not repeated in this release |

## Installation

Use Python 3.12 or later. For a general runnable installation:

```bash
python -m venv .venv
# Activate with .venv/bin/activate on POSIX, or .venv/Scripts/Activate.ps1 on PowerShell.
python -m pip install -e ".[models]"
python -m unittest discover -s tests -v
python -m adhd_portfolio demo --out artifacts/demo-001
```

`requirements-fmri-verified.txt` records the exact locally exercised Windows CPU dependencies. `pyproject.toml` supplies broader installation constraints for the example. Broad compatibility is not numerical equivalence: the full frozen runner checks exact recorded package versions and the nilearn numerical source hash before execution. A clean dependency installation on another OS has not been verified. Historical notebook dependencies are separate from this package.

The original runtime installed nilearn 0.12.1, nibabel 5.3.2 and packaging 25.0 in a separate vendor folder. For an existing such environment, set `ADHD_NILEARN_VENDOR` to that folder. This optional path is not required when those distributions are installed normally; do not point it at untrusted Python code.

## Public evidence

`results/fmri_378/` contains fold/repeat summaries, selected alphas, paired differences and aggregate learning curves. `verification.json` records the input hashes and passed replay scope. It contains no participant IDs or predictions. Reading the public table is not equivalent to replaying private prediction rows.

## Recompute the frozen evidence

The local archival release is named `ADHD_fMRI_frozen_2026-09-08` and includes `MANIFEST.json` and three `runs/` directories. It is separate from the repository and is not publicly redistributed.

```bash
python -m adhd_portfolio verify --release /path/to/ADHD_fMRI_frozen_2026-09-08 --out artifacts/evidence-001
```

The verifier checks manifest hashes for every file it uses, role/label/site consistency, exactly one test prediction per person/model/repeat, matching cohorts across stages, fold and repeat aggregation, and all 60 validation-selected weights. Outputs are written only after every check passes. This is table-level independent replay, not independent reconstruction of raw preprocessing or refitting of every model.

The first incremental analysis multiplied float32 MLP predictions before adding float64 LR probabilities. The replay preserves that operation order and precision rather than silently widening tolerance. Historical linear margins are averaged as fold AUCs; they are not pooled across folds.

## Full runtime inputs and explicit execution

The runner relocates the archived modules' data paths in memory and preserves their source bytes. It expects an authorized local runtime layout:

```text
runtime/runs/
  connectome_representations_20260907_165559/cohort.csv
  functional_fusion_20260907_124543/{cohort.csv,splits.csv,verification.json}
  temporal_cache_20260907_113751/{cohort.csv,timeseries.npz,verification.json}
  features_20260907_111310/{features.npz,verification.json}
```

The time-series NPZ requires data, offsets, lengths and subject_id; the feature NPZ requires subject_id, label, fc_summary and fc_edges. Original loaders validate cache hashes, IDs, labels and prior verification status. These are audited derived inputs, not raw BIDS files. Existing historical preprocessing notebooks are retained, but rebuilding these exact inputs from raw scans in a new environment has not been validated by this release.

Start with preflight; it reports missing inputs and environment differences without training:

```bash
python -m adhd_portfolio frozen --runtime-root /path/to/runtime --stage representation --out /separate/path/repeated-new
```

Prepare splits only (output must be new and outside the runtime):

```bash
python -m adhd_portfolio frozen --runtime-root /path/to/runtime --stage representation --out /separate/path/prepare-new --prepare-only
```

With inputs and environment matched, a deliberate complete rerun uses three stages:

```bash
python -m adhd_portfolio frozen --runtime-root /path/to/runtime --stage representation --out /separate/path/repeated-new --execute
python -m adhd_portfolio frozen --runtime-root /path/to/runtime --stage site_motion_increment --parent /separate/path/repeated-new --out /separate/path/increment-new --execute
python -m adhd_portfolio frozen --runtime-root /path/to/runtime --stage demographic_increment --parent /separate/path/increment-new --out /separate/path/demographic-new --execute
```

Do not reuse the prepare-only directory for training. The wrapper refuses existing outputs and writes no source or input changes. Full training can be expensive; its duration and peak RAM were not measured by this packaging task. Stage 2 requires the parent checkpoints; stage 3 requires parent validation predictions and the fuller demographic metadata. The original archived cohort must already contain these audited fields.

## Source and evidence boundaries

- Eleven scientific modules are byte-identical to the archived release. A twelfth, `run_paired.py`, is a transitive import omitted by the old archive; it is separately labeled as a runtime supplement in `sources.json`.
- Only the three selected entry points are supported through the wrapper. Other preserved modules are import dependencies, not newly supported standalone commands.
- Original repeated-MLP seeds depend on fold, not repeat; the same three seed identities are reused across repeats. This historical choice is preserved, not silently changed.
- Five repeats reuse participants. SD/ranges are descriptive. This package adds no claim of a formal independence-adjusted CI, equivalence, calibration or external validation.
- [Version index](docs/portfolio/RESULT_VERSIONS.md) separates 409-person history, 378-person fMRI and structural/fusion cohorts.

## Rebuild presentation artifacts

```bash
python -m pip install -e ".[slides]"
python scripts/build_portfolio_assets.py
```

The generator reads the verified aggregate CSVs and produces an editable 10-slide PPTX with Chinese speaker notes, a single-page English PDF, and the SVG result chart. The slide bounds and headline values are checked during generation; every page was also rendered and visually inspected locally. CI configuration is provided but its GitHub-hosted run has not occurred in this local task.
