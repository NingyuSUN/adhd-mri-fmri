## 2026-09-10 — fMRI career portfolio packaging

- Added current 378-person representation and demographic-control evidence, separate from 409-person and structural history.
- Preserved scientific source hashes; added CLI evidence replay, synthetic demo and path-only runtime wrappers.
- Added correctness tests, reproduction levels, case study, technical deck and demo walkthrough.
- Replayed frozen predictions; no new full fMRI training or changes to the running structural v2.

# Changelog

## 2026-09-10 — Structural + functional late-fusion analysis

- Added a QC-locked paired analysis retraining structural (98 region/TIV volumes), functional (A424 tangent) and non-imaging models together on one frozen protocol, three prespecified cohorts (`primary` 350, `warning_free` 302, `include_holds` 375) and the original 5×3 subject-level splits.
- 45 folds × 17 models/fusions, all independently replay-verified (`verification.json` status `verified`); run and verified end-to-end on one Linux host.
- Added `docs/structural_functional_fusion.md`, `results/structural_functional_fusion_summary.csv`, `results/structural_functional_fusion_paired_deltas.csv`, and a `RESULTS.md` section.
- Finding is consistent with the frozen benchmark: non-imaging confounds (AUC ≈ 0.71) dominate; neither functional nor structural imaging adds stable incremental value; the only positive image-derived increment (structural added to the image-only functional model) is robust only in `primary`.

## 2026-09-04 — Final benchmark release

- Added the completed repeated site-and-label-stratified portfolio benchmark (`n=409`, 20 outer evaluations).
- Added `09_portfolio_site_stratified_cv.ipynb` and its aggregate result table.
- Locked the strict nested LOSO fMRI benchmark.
- Added confound, motion-restricted, residualized, within-site, scrubbing, and spatial-module results.
- Documented the decision not to proceed with Transformer fine-tuning after the frozen representation failed the transfer gate.
- Added aggregate result tables, final report, limitations, reproducibility checklist, and model card.
- Marked the project complete as a confound-aware negative/boundary research result.

## 0.1.0 — 2026-05-21

Initial research-oriented GitHub file set.

Added:

- professional README
- data documentation
- methods documentation
- results template
- limitations
- reproducibility guide
- roadmap
- cleaned notebook/script naming
- requirements files
- GitHub about/topic suggestions
