# Changelog

## 2026-09-18 — ROI biological rationale and exploratory feature-subset comparisons

- Added `docs/paper/ROI_BIOLOGICAL_RATIONALE_AND_EVIDENCE.md`, which maps the early ROI-guided CNN's region choice to the fronto-striatal-thalamic circuit literature (PubMed citations with DOIs) and traces the atlas behind each later feature set: SynthSeg 2.0 for the 98 structural volumes (including the exact 3 columns dropped from the 101-measurement output) and BrainLM's Glasser HCP-MMP + subcortical + cerebellar A424 atlas for the 424 functional nodes.
- Added two exploratory CV comparisons of a literature-motivated subset against the full feature set, reusing the frozen splits and cohorts: `reproduction/exploratory/structural_biological_subset_cv.py` (36 of 98 regions) and `reproduction/exploratory/a424_biological_subset_cv.py` (148 of 424 nodes), with atlas reference files under `reproduction/exploratory/a424_atlas_reference/` and outputs in `results/*_biological_subset_cv_20260918/`.
- Summarized both comparisons in `FINAL_REPORT.md` and `README.md`. They are single exploratory runs outside the confirmatory statistical framework; the repeat counts are descriptive, not significance claims.

## 2026-09-17 — Update stale methodology docs

- Rewrote `METHODS.md`, which still described only the project's original single-slice/ROI-CNN plan from May 2026. It now documents the actual final pipeline: A424-based fMRI representations (FC, spectral, GNN, frozen BrainLM, end-to-end temporal models), the structural branch through pretrained Swin-T, structural+functional late fusion, and the two-framework evaluation design (repeated site-stratified CV as the primary portfolio metric, strict LOSO as the robustness stress test) plus the v2 statistical framework (Nadeau–Bengio intervals, TOST equivalence).
- Removed `docs/structural_mri_pipeline.md`, `docs/fmri_gnn_pipeline.md`, `docs/model_evaluation.md`, and `docs/ablation_and_site_bias.md` — orphaned early-design notes (referenced from nowhere else in the repository) describing the same superseded pipeline; their still-valid content is folded into the rewritten `METHODS.md`.
- Fixed `MODEL_CARD.md`, which labeled strict LOSO as the "primary design" (contradicting `README.md`'s actual framing of repeated CV as the primary portfolio metric and LOSO as the stress test) and omitted the CV-portfolio and structural-MRI headline numbers entirely.

## 2026-09-17 — Remove internal working notes; neutral wording

- Removed six `docs/paper/` files that were internal AI-assisted-workflow logs rather than reader-facing documentation (a cross-session handoff note, a raw AI reviewer transcript and its adjudication table, a task-authorization log, a package-validation log, and a post hoc analysis plan written as an internal checklist). Their non-redundant scientific content (the NYU pair-weight correction, methods deviations, TRIPOD+AI gaps) is already preserved in `STATISTICAL_INTERPRETATION.md`, `CLAIMS_EVIDENCE_20260914.md`, `SENSITIVITY_RESULTS.md`, `METHODS_CLARIFICATION_20260914.md`, and `TRIPOD_AI_GAPS_20260914.md`.
- Removed `docs/github_about.md`, a stale pre-launch scratch note superseded by the repository's actual description/topics/badges.
- Replaced "recruiter-safe" wording in `README.md`, `demo/README.md`, `docs/ENGINEERING.md`, and `tools/portfolio_quickstart.py` with neutral technical language ("aggregate-only" / "public").
- Replaced the internal server codename with generic wording in `docs/analysis_v2_deviations.md`, `docs/analysis_v2_protocol.md`, `docs/paper/FRESH_REPRODUCTION_STATUS.md`, and two source manifests (with a matching `PACKAGE_MANIFEST.json` hash/byte-count update for the one manifest that is itself hash-verified).

## 2026-09-16 — Portfolio/discoverability polish

- Set the GitHub repository description and topics (previously blank, which hurt discoverability).
- Added a CI-status badge and an MIT license badge to `README.md`.
- Retitled `CITATION.cff` from a result-implying title to a neutral, TRIPOD+AI-aligned one (title previously read as a positive-result claim; the finding is a confound-aware negative/boundary result).
- Added a "Confirmatory statistics and self-audit (analysis v2)" section to `PORTFOLIO_CASE_STUDY.md` — the pre-registration, external review, strict-LOSO re-analysis, and public self-correction of a reporting error were previously undocumented there.

## 2026-09-14 — Portfolio engineering release

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


## 2026-09-11 — Analysis v2: pre-registered confirmatory statistics

- Re-ran the structural + functional late-fusion analysis under a pre-registered protocol (`docs/analysis_v2_protocol.md`, finalized after an independent methods/statistics review): repeat-dependent MLP seed, symmetric primary contrast (`full_fusion_structural_mlp` − `full_functional_mlp`), Nadeau–Bengio corrected 90% intervals for the CV deltas, a pre-registered TOST equivalence test (margin ±0.02 AUC), and a full strict leave-one-site-out re-run.
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

- Added the completed repeated site-and-label-stratified portfolio benchmark (`n=409`, 20 outer evaluations).
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
