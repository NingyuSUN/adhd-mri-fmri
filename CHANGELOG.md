# Changelog

## 2026-11-02 — v1.0.0: wording, English documents and layout

- First tagged release, `v1.0.0`. `CITATION.cff` now records version 1.0.0, the release date, license, repository URL, abstract and keywords.
- Terminology: the analysis v2 protocol, results and deviation log were first published together in `aad605a`, and the protocol was not registered externally, so reader-facing documents now call it *prespecified*. The protocol and deviation log keep their frozen wording under a dated note, which also states that the cited `coordination/gemini/v2protocol_review_20260910/REVIEW.md` is an internal file not included here. Earlier entries in this changelog were reworded to match; hash-bound refit reports keep their original text.
- The Gemini 3.1 Pro check of the protocol is described as an AI-assisted methods review, not an independent or external review.
- Published the remaining Chinese documents in English: `docs/paper/LITERATURE_AND_NEXT_STEPS_20260916.md` (formerly `_ZH`) and the tables-and-figures notes and index. The package README is now `results/tables_figures_20260914/README_TABLES_AND_FIGURES.md`; the generator scripts carry the same English text, and `PACKAGE_MANIFEST.json` is updated for the four changed files. Tables, figures and source data are unchanged. The manifest's `head` field still records the pre-revision commit `40a4bb9`, which no longer resolves on GitHub; package integrity is checked by the file hashes.
- Moved `CASE_STUDY`, `DATA`, `FINAL_REPORT`, `LIMITATIONS`, `METHODS`, `MODEL_CARD`, `PROJECT_STATUS`, `REPRODUCIBILITY`, `RESULTS` and `ROADMAP` into `docs/`, rewrote every relative link and added `docs/README.md`. Links pinned to earlier commits still resolve; links to these files on `main` need the `docs/` prefix.
- Added `reproduction/tests/test_headline_numbers.py`, which checks the README headline table against `docs/RESULTS.md` and the summaries.
- CI also runs the standard-library quickstart and artifact validator on Python 3.10 and 3.12, matching the README.
- Recorded in `reproduction/VENDORED_SOURCES.md` that the vendored Nilearn, NiBabel and Packaging sources are byte-identical to the official wheels; the reproduction guide no longer calls them patched.
- Set the repository homepage to the project evidence guide and changed "pre-registered" to "prespecified" in the repository description.

## 2026-10-16 — English evidence documents

- Rewrote `docs/paper/ROI_BIOLOGICAL_RATIONALE_AND_EVIDENCE.md` in English as reader-facing documentation. The atlas verification, literature mapping, exploratory results and limitations are unchanged; process notes about how the records were checked were removed, and the second section "3c" is now "3d".
- Translated the TRIPOD+AI gap table in `docs/paper/TRIPOD_AI_GAPS_20260914.md` into English.
- Removed references to branches that are not published in this repository.

## 2026-10-15 — Evidence links repinned after the history revision

- The public history was revised in October 2026: commit IDs changed and commit times were kept. `docs/PROJECT_EVIDENCE.md` was repinned to the published commits. Links made before the revision translate as follows:

| Earlier commit | Published commit | Used for |
|---|---|---|
| `84629eaac0e3e621e3002d6259f769e03e8515ec` | `2cfc942f81d481eb2c17cc79e18dd7ffd62a8f62` | 24 September evidence baseline |
| `755266f388f73955c58a86e8a81b13197052a303` | `d9093c69808fe1591506a06e4f652b71005ca3a9` | Archived GCN/GAT notebook source |

## 2026-10-13 — Evidence guide on the homepage

- Added `docs/PROJECT_EVIDENCE.md`, which connects ownership, the historical GCN/GAT implementation, the controlled imaging benchmarks and the recorded feature-level replay, with the limits of each, and linked it from the top of `README.md`.

## 2026-09-24 — Naming cleanup

- Renamed the case study to `CASE_STUDY.md`, the aggregate quickstart to `tools/quickstart.py` (report schema `quickstart.v1`, default output `artifacts/quickstart`), and the site-stratified CV summary to `results/fmri_benchmark_stratified_cv_summary.csv`. Wording now describes the work as a research benchmark.
- Added `docs/paper/LITERATURE_AND_NEXT_STEPS_20260916_ZH.md`: a targeted comparison with six published ADHD-200/neuroimaging studies and a proposed four-stage follow-up plan, rewritten for public readers.

## 2026-09-18 — ROI biological rationale and exploratory feature-subset comparisons

- Added `docs/paper/ROI_BIOLOGICAL_RATIONALE_AND_EVIDENCE.md`, which maps the early ROI-guided CNN's region choice to the fronto-striatal-thalamic circuit literature (PubMed citations with DOIs) and traces the atlas behind each later feature set: SynthSeg 2.0 for the 98 structural volumes (including the exact 3 columns dropped from the 101-measurement output) and BrainLM's Glasser HCP-MMP + subcortical + cerebellar A424 atlas for the 424 functional nodes.
- Added two exploratory CV comparisons of a literature-motivated subset against the full feature set, reusing the frozen splits and cohorts: `reproduction/exploratory/structural_biological_subset_cv.py` (36 of 98 regions) and `reproduction/exploratory/a424_biological_subset_cv.py` (148 of 424 nodes), with atlas reference files under `reproduction/exploratory/a424_atlas_reference/` and outputs in `results/*_biological_subset_cv_20260918/`.
- Summarized both comparisons in `FINAL_REPORT.md` and `README.md`. They are single exploratory runs outside the confirmatory statistical framework; the repeat counts are descriptive, not significance claims.

## 2026-09-17 — Update stale methodology docs

- Rewrote `METHODS.md`, which still described only the project's original single-slice/ROI-CNN plan from May 2026. It now documents the actual final pipeline: A424-based fMRI representations (FC, spectral, GNN, frozen BrainLM, end-to-end temporal models), the structural branch through pretrained Swin-T, structural+functional late fusion, and the two-framework evaluation design (repeated site-stratified CV as the primary metric, strict LOSO as the robustness stress test) plus the v2 statistical framework (Nadeau–Bengio intervals, TOST equivalence).
- Removed `docs/structural_mri_pipeline.md`, `docs/fmri_gnn_pipeline.md`, `docs/model_evaluation.md`, and `docs/ablation_and_site_bias.md` — orphaned early-design notes (referenced from nowhere else in the repository) describing the same superseded pipeline; their still-valid content is folded into the rewritten `METHODS.md`.
- Fixed `MODEL_CARD.md`, which labeled strict LOSO as the "primary design" (contradicting `README.md`'s actual framing of repeated CV as the primary metric and LOSO as the stress test) and omitted the stratified-CV and structural-MRI headline numbers entirely.

## 2026-09-17 — Remove internal working notes; neutral wording

- Removed six `docs/paper/` files that were internal working notes rather than reader-facing documentation. Their non-redundant scientific content (the NYU pair-weight correction, methods deviations, TRIPOD+AI gaps) is already preserved in `STATISTICAL_INTERPRETATION.md`, `CLAIMS_EVIDENCE_20260914.md`, `SENSITIVITY_RESULTS.md`, `METHODS_CLARIFICATION_20260914.md`, and `TRIPOD_AI_GAPS_20260914.md`.
- Removed `docs/github_about.md`, a stale pre-launch scratch note superseded by the repository's actual description/topics/badges.
- Replaced informal wording in `README.md`, `demo/README.md`, `docs/ENGINEERING.md`, and `tools/quickstart.py` with neutral technical language ("aggregate-only" / "public").
- Replaced the internal server codename with generic wording in `docs/analysis_v2_deviations.md`, `docs/analysis_v2_protocol.md`, `docs/paper/FRESH_REPRODUCTION_STATUS.md`, and two source manifests (with a matching `PACKAGE_MANIFEST.json` hash/byte-count update for the one manifest that is itself hash-verified).

## 2026-09-16 — Discoverability polish

- Set the GitHub repository description and topics (previously blank, which hurt discoverability).
- Added a CI-status badge and an MIT license badge to `README.md`.
- Retitled `CITATION.cff` from a result-implying title to a neutral, TRIPOD+AI-aligned one (title previously read as a positive-result claim; the finding is a confound-aware negative/boundary result).
- Added a "Confirmatory statistics and self-audit (analysis v2)" section to `CASE_STUDY.md` — the prespecified protocol, AI-assisted methods review, strict-LOSO re-analysis, and public self-correction of a reporting error were previously undocumented there.

## 2026-09-14 — Engineering release

- Added an aggregate-only quickstart CLI and deterministic JSON/Markdown report for reviewers without private MRI access.
- Added public-artifact validation for manifest hashes, table/figure counts, schema safety, and private-path redaction.
- Added locked-environment CI, a `Makefile`, engineering documentation, and a five-minute reviewer path.
- Removed notebook-era exploration code, unused notebook helpers, and superseded top-level environments from the final branch; Git history retains them.
- Kept raw MRI, subject-level predictions, checkpoints, and full replay inputs outside the public repository.

## 2026-09-11 — Post hoc statistical interpretation and sensitivity audit

- Preserved the original v2 protocol and numerical decisions; corrected the interpretation to state that the primary equivalence hypothesis was not confirmed.
- Corrected NYU's primary case-control pair weight to 67.07%; approximately 40% was its participant fraction.
- Added matched-subject/fixed-weight QC decomposition, a symmetric final-fusion-weight decomposition, and validation-only conditional selector stability.
- Recomputed the five original statistical/calibration tables and original decision exactly in a clean statistics environment.
- Added the full source/dependency closure and a separate fresh-fit runner. Full-training completion is recorded by its execution report, not inferred from this changelog.
- This audit supersedes the causal and LOSO-validity interpretations in the historical entry below. The three pairwise cohort overlaps are 86.3%, 93.3%, and 80.5% when expressed as intersection/union, not all above 85%.


## 2026-09-11 — Analysis v2: prespecified confirmatory statistics

- Re-ran the structural + functional late-fusion analysis under a prespecified protocol (`docs/analysis_v2_protocol.md`, finalized after an AI-assisted methods/statistics review): repeat-dependent MLP seed, symmetric primary contrast (`full_fusion_structural_mlp` − `full_functional_mlp`), Nadeau–Bengio corrected 90% intervals for the CV deltas, a prespecified TOST equivalence test (margin ±0.02 AUC), and a full strict leave-one-site-out re-run.
- 45 mixed-site CV folds + 21 LOSO units × 3 cohorts, independently consistency-verified (`reproduction/legacy/verify_v2.py`, 66 units).
- Result: mixed-site CV point estimates confirm the direction (every confound-plus-imaging contrast negative) but the corrected 90% interval for the primary contrast is [−0.040, +0.017] — formal equivalence is underpowered at n=350. Strict LOSO is uninformative: the held-out summary ΔAUC swings +0.028 / −0.086 / −0.043 across three QC cohorts sharing >85% of subjects, dominated by NYU's subject composition.
- Documented why ADHD-200 (7 sites, one dominant, two below n=15) cannot support strict LOSO for a small AUC effect, which is the empirical basis for using repeated site-stratified CV as the primary endpoint.
- Added `docs/analysis_v2_{protocol,results,deviations}.md`, `results/v2_*.csv`, `figures/v2_F{1,2,3}_*.png`, the source files now retained under `reproduction/legacy/`, and a `RESULTS.md` section.

## 2026-09-10 — Structural + functional late-fusion analysis

- Added a QC-locked paired analysis retraining structural (98 region/TIV volumes), functional (A424 tangent) and non-imaging models together on one frozen protocol, three prespecified cohorts (`primary` 350, `warning_free` 302, `include_holds` 375) and the original 5×3 subject-level splits.
- 45 folds × 17 models/fusions, all independently replay-verified (`verification.json` status `verified`); run and verified end-to-end on one Linux host.
- Added `docs/structural_functional_fusion.md`, `results/structural_functional_fusion_summary.csv`, `results/structural_functional_fusion_paired_deltas.csv`, and a `RESULTS.md` section.
- Finding is consistent with the frozen benchmark: non-imaging confounds (AUC ≈ 0.71) dominate; neither functional nor structural imaging adds stable incremental value; the only positive image-derived increment (structural added to the image-only functional model) is robust only in `primary`.

## 2026-09-04 — Final benchmark release

- Added the completed repeated site-and-label-stratified benchmark (`n=409`, 20 outer evaluations).
- Added the repeated site-stratified analysis and its aggregate result table. Its exploratory notebook was later removed from the final branch.
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
