# fMRI portfolio implementation plan

**Goal:** Execute the user-approved career portfolio route from the September 10 integrated strategy.
**Architecture:** Preserve frozen scientific sources; add a small package for strict evidence replay, a synthetic ML/DL smoke example, and explicit path relocation for authorized-data reruns. Generate public aggregates and presentations from verified outputs.
**Tech stack:** Python, pandas/NumPy/scikit-learn/PyTorch/nilearn, unittest, editable PPTX.
**Spec:** User approved route 2: latest results, runnable code, reproducibility, correctness checks, one-page case, technical slides and short demo; both medical-AI and general DS/MLE narratives.

## Constraints
- No edits to frozen runtime, data, training protocols or running structural v2.
- No individual data/checkpoints in public artifacts; no GitHub push in this task.
- Keep 378-person fMRI distinct from historical 409 and structural cohorts.
- Repeat ranges are not CIs; no external-validation/clinical claim for current fMRI.

## Tasks
- [x] Preserve archived source bytes and hash inventory. Identify omitted transitive dependencies explicitly.
- [x] Tests: reject subject/role leakage, duplicate/missing predictions, label mismatch and malformed model coverage. Test AUC aggregation with independently known examples.
- [x] Implement evidence CLI: validate all three frozen run tables; recompute fold/repeat metrics; replay validation alpha selection and test-score arithmetic; export aggregates only.
- [x] Tests: unchanged training preprocessing after perturbing held-out inputs; alpha tie policy; synthetic training and checkpoint predictions.
- [x] Add frozen runtime loader and non-destructive path wrapper; preflight inputs and environment, refuse reused output directories; run prepare-only on existing cohort, no original full training.
- [x] Synthetic demo: existing LR/MLP implementation, explicit synthetic data, checkpoint replay, learning curves and measured resource context.
- [x] Update README, results/version index, model card, reproducibility and one-page career case. Preserve historical evidence in clearly labeled paths.
- [x] Generate 10-slide English technical deck with Chinese presenter notes plus demo transcript; inspect rendered pages and numerical content.
- [x] Run unit/integration tests, source hashes, real prediction replay, package import and CLI, source/diff/private-file audit; record exact limitations and completion.

## Completion evidence

- 19 unit tests passed; synthetic LR/MLP training and checkpoint replay passed.
- Real-data prepare-only succeeded and all three frozen stages passed input/environment preflight.
- 35,910 test rows and 60 validation weight choices replayed; aggregate errors at floating-point precision.
- Wheel build/install/import passed using existing recorded dependencies; no clean dependency install or full retraining claimed.
- Editable 10-slide deck with Chinese notes and single-page PDF generated, rendered and visually inspected.
- Independent read-only review found an omission in validation-file ignore patterns; both patterns were added. No other important numerical/path issues reported.
- New aggregates/source inventory checked for participant-level records and exact source bytes; structural v2 and original frozen runtime remained untouched.
