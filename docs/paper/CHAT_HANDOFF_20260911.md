# ADHD MRI/fMRI — compact conversation and research handoff

Date: 2026-09-11. This is a condensed record of the conversation, its decisions, scientific findings, implementation, and outstanding work. Runtime counts below are timestamped observations, not promises of current completion. No credentials or participant-level records are included.

## 1. User requests and agreed scope

The user reported substantial new GitHub work and that the server folder had changed from ADHD200 to ML. They asked to reload the project, update its context, assess the distance to a publishable paper, and then explicitly carry out **statistical interpretation, sensitivity decomposition, and complete reproduction**. Later they requested a runtime estimate, a compact context summary, and this Markdown document stored on DocStash. The user restarted Codex to make DocStash available.

Work was authorized on the existing project. Original frozen protocols, inputs, predictions, source versions, and decisions were to remain unchanged. New analysis and fresh fitting were isolated. No duplicate training, unrequested model search, test-set selection, public participant-data upload, or GitHub push was authorized by this work. The earlier teaching deck remains fMRI-only; structural/functional fusion is a separate scope.

## 2. Project locations and version state

| Item | Location or version |
|---|---|
| Server | `seedna2@SV002` |
| Renamed server root | private server root on SV002 (path withheld) |
| Original private analysis workspace | private analysis workspace on SV002 (path withheld) |
| Structural preprocessing workspace | private preprocessing workspace on SV002 (path withheld) |
| Frozen original multimodal run | `runs/structural_fusion_v2_20260910` beneath the private analysis workspace |
| Separate reproduction root | private reproduction root on SV002 (path withheld) |
| Fresh fitting output | private fresh-fit directory on SV002 (path withheld) |
| Original local Git checkout | local original checkout (path withheld) |
| Isolated worktree | local isolated worktree (path withheld) |
| Separate local private files | local private collection directory (path withheld) |
| Working branch | `paper-hardening-20260911` |
| Base main commit when work began | `7cd84899a5d81ffd9a391885ba27d20dc851f02e` |
| Plan commit | `7129da8` |
| Analysis/reproduction-workflow commit | `40a4bb9` |

The existing original checkout was left unchanged. The new work was committed locally, without pushing or merging. This chat-handoff document was added afterward and is not included in commit `40a4bb9`. Adjacent `adhd-local` runtime directories are not Git roots. The September 11 handoff superseded older notes that said the original v2 run was still training.

## 3. Publication assessment and interpretation

The project has a substantial computational evidence base, but reproducibility alone does not establish scientific validity or publication readiness. The defensible paper needs a clear primary question, accurate uncertainty statements, disclosure of data reuse and protocol deviations, and an explanation of robustness failures. External validation and independent anatomical/statistical review remain separate gaps. No acceptance probability, journal guarantee, clinical utility, or general absence of brain-imaging signal was established.

The primary contrast is **full_fusion_structural_mlp minus full_functional_mlp**. Three QC cohorts contain 350 primary, 302 warning-free, and 375 include-holds participants. The design includes 45 repeated-CV folds and 21 LOSO units, with 17 model outputs per unit.

| Primary-cohort analysis | Mean ΔAUC | 90% interval | Defensible interpretation |
|---|---:|---|---|
| CV, original corrected estimator, df=14 | −0.011391 | [−0.040031, +0.017249] | Does not establish equivalence within ±0.02 |
| CV, original df=2 sensitivity | −0.011391 | [−0.058871, +0.036090] | Material positive and negative differences remain compatible |
| CV, actual fitted-row ratio sensitivity, df=14 | −0.011391 | [−0.043066, +0.020284] | Conclusion depends partly on variance-correction convention; still no equivalence |
| LOSO, original conditional bootstrap | +0.027536 | [+0.009470, +0.046258] | Positive conditional contrast, but lower bound does not establish benefit above +0.02 |

Important corrections and limits:

- The protocol required equivalence in both CV and LOSO; that requirement was not satisfied.
- The original machine-readable audit/falsification trigger was preserved. Conflicting results must not simply be dismissed as an artifact or as proof that LOSO is invalid.
- The historical `meaningful_increment` branch label is stronger than the interval supports. Positivity, materiality, and equivalence must be reported separately.
- The written B2/B4 conditions overlap; the executed ordered branches choose B2. The original program and decision were not rewritten.
- Changing signs across QC cohorts does not rule out leakage. Direct split/data-flow checks and provenance are needed.
- Original LOSO uncertainty conditions on observed sites and trained models. It does not include retraining variability or sampling new acquisition sites.
- A frozen analysis file is not proof of externally timestamped prospective registration. v2 reuses previously examined data; new sensitivity analyses are explicitly post hoc.
- LOSO used one stratified 85/15 inner holdout rather than the written inner 3-fold/refit plan. This deviation remains disclosed.
- Secondary comparisons are exploratory/sensitivity analyses; negative results do not automatically remove multiplicity concerns.
- Overlapping QC cohorts and repeated predictions of the same participant are not independent replications.

## 4. Completed sensitivity decomposition

Matched-subject analysis holds evaluation people and primary-cohort site weights fixed. It exactly decomposes each native pair-weighted change into a common-subject fitted-pipeline contribution, evaluation-composition contribution, and site-weight contribution. Residuals are zero to floating-point precision.

| QC transition | Shared participants | Total shift | Fitted-pipeline contribution | Evaluation composition | Site weights |
|---|---:|---:|---:|---:|---:|
| Primary → warning-free | 302 | −0.113186 | −0.118894 | +0.003795 | +0.001913 |
| Primary → include-holds | 350 | −0.070457 | −0.065327 | −0.003533 | −0.001596 |
| Warning-free → include-holds | 302 | +0.042729 | +0.057892 | −0.011653 | −0.003510 |

Thus evaluation composition and aggregation weights alone do not explain the reversal. A second, symmetric two-factor decomposition cross-applies the original validation-selected final fusion weights to both cohorts' fixed predictions on common test participants:

| Transition | Common-subject pipeline shift | Prediction contribution | Final fusion-alpha contribution |
|---|---:|---:|---:|
| Primary → warning-free | −0.118894 | +0.003978 | −0.122872 |
| Primary → include-holds | −0.065327 | −0.021565 | −0.043762 |
| Warning-free → include-holds | +0.057892 | −0.021412 | +0.079305 |

Final-alpha selection dominates the primary→warning-free change under this descriptive allocation. The nonlinear interaction is shared symmetrically between factors. This is not a causal experiment; upstream training/tuning and earlier functional fusion selection remain bundled in the prediction component.

### NYU and final-selector stability

A reporting error was corrected: NYU contains 139/350 = 39.7% of participants but contributes 4,774/7,118 = **67.07% of within-site case-control pairs**, not approximately 40%. Published pair counts and numeric aggregate estimates were already correct.

A validation-only, site-by-label bootstrap used 1,000 resamples for each of all 66 units. Fitted models and upstream selections were fixed. The original alpha grid and tie-breaking rule were preserved; test scores did not select alpha.

| NYU QC cohort | Original structural alpha | Validation n | Probability of reselecting original alpha | Probability alpha=0 |
|---|---:|---:|---:|---:|
| Primary | 0 | 32 | 92.0% | 92.0% |
| Warning-free | 1 | 29 | 50.9% | 20.1% |
| Include-holds | 0.25 | 33 | 33.7% | 42.2% |

These are conditional selector-sensitivity results. Associated test-delta quantiles are not confidence intervals for the entire training procedure. No new preferred cohort or model was chosen from test outcomes.

## 5. Reproduction: completed versus pending

### Completed evidence

- A clean environment regenerated the original 42-row CV contrast table, 84-row LOSO contrast table, 147-row site table, 120-row calibration-bin table, and 12-row calibration summary. All numeric differences were zero.
- Original `decision.json` reproduced exactly; three original figures regenerated.
- New aggregate sensitivity outputs and four publication figures were generated and visually checked.
- All 378 within-participant covariances were freshly recomputed from frozen time series and were byte-identical to the reference.
- First fresh CV unit completed in about 981 seconds. All 17 model outputs matched exactly: maximum score difference 0.0 for 765 validation rows and 2,006 test rows; selected fusion weights were identical.
- Source closure contains 468 hash-verified frozen files, including transitive modules and the original vendored geometry dependencies/licenses. All nine protocol-listed source hashes matched.
- A post hoc reference manifest binds 910 CSV/JSON records, including all 12 derived cohort/split files. This is provenance evidence, not prospective registration.
- Nineteen local engineering tests passed. A clean server audit environment also reproduced the original statistics and figures.

### Full fitting status recorded in this chat

At **2026-09-11 02:54 UTC / 11:54 Japan time**, the live server reported **7/66 units completed**, with six workers continuing. Observed parallel-unit runtimes were about 24–29 minutes. The estimate given then was **another 5–7 hours**, approximately **17:00–19:00 Japan time**, allowing for larger LOSO training sets and final validation. This was an estimate, not a deadline or completion statement.

When preparing this archive, the saved local status page still described the run as pending, and `collection_status.json` said `waiting_for_server_final_verification`. Those files alone do not prove that either process remains alive after the Codex restart. Full 66-unit completion has not been established in this document; inspect live state and final proof before making that claim.

### Boundary of “complete reproduction”

This is fresh execution of hash-identical training code, starting from frozen A424 time-series and regional-volume derivatives. It recomputes covariance, training-only geometry/features/confounds/scalers, fits LR/MLP models, performs validation selection, and compares held-out outputs. It is not an independently authored algorithm, raw MRI reprocessing, new segmentation, expert anatomical QC, or external validation.

## 6. Independent review and completion safeguards

Statistical review found no actionable computation errors. It independently checked decomposition identities, normalized selector probabilities, and the absence of original LOSO cross-class score ties. New bootstrap code explicitly handles ties.

Reproduction review identified gaps that were repaired and regression-tested:

1. Bind the derived fitting metadata and explicitly verify the raw time-series hash.
2. Publish terminal success only after summaries succeed; failed re-verification clears stale success.
3. Publish per-unit completion transactionally after logs close, binding comparison and artifact hashes.
4. Verify resumed job identity and protocol, preventing a valid completed fold from being reused as a different fold.
5. Reject output paths that could write into the original run/source workspace.
6. Distinguish newly computed covariance from cache reuse on a later invocation.

The already-running driver was not silently replaced. Its exact source is preserved in `reproduction/execution_history/reproduce_v2_launched_20260911.py`. Reviewed tools were deployed separately. The independent final gate checks all 66 units, roles, 17-model validation/test predictions, alpha selections, summaries, statistical tables, decision, and figures before publishing `verified_reproduction.json`.

A one-shot finisher waits for the existing training process to exit, including aggregation. A separate collector retrieves only verified aggregate outputs and updates the local status page after success. A failed gate or connection must remain visibly pending/failed; a process ID or provisional report alone is insufficient.

## 7. Artifact index

Paths below are relative to the isolated worktree listed in section 2.

- `docs/paper/STATISTICAL_INTERPRETATION.md` — corrected interpretation and limitations.
- `docs/paper/SENSITIVITY_RESULTS.md` — quantitative decomposition and selector results.
- `docs/paper/FRESH_REPRODUCTION_STATUS.md` — execution snapshot, replaced after verified collection.
- `docs/paper/PLAN_20260911.md` — authorized post hoc plan and open acceptance items.
- `results/paper_readiness_20260911/` — aggregate tables and statistical verification.
- `figures/paper_readiness_20260911/` — four new PNG/PDF figures: QC decomposition, site contributions, CV interval sensitivity, NYU selector stability.
- `reproduction/README.md` — environments, commands, provenance, resume rules, and boundaries.
- `reproduction/reproduce_v2.py` — reviewed fresh-fitting driver.
- `reproduction/verify_fresh.py` — independent final completion gate.
- `reproduction/finish_execution.py` — waits for existing training and runs the gate; never launches training.
- `reproduction/requirements-runtime.lock` and `requirements-statistics.lock` — pinned environments.
- `results/paper_readiness_20260911/fresh_refit/` — expected destination of final verified aggregate exports; existence/completion must be checked.

Server state/log files beneath the reproduction root:

- `fresh_v2/reproduction_status.json`
- `fresh_v2/pipeline_status.json`
- `fresh_v2/verification_status.json`
- `fresh_v2/verified_reproduction.json` — required final proof
- `all_units.log`, `final_verification.log`
- `fresh_statistics_verified/` — expected final regenerated statistics

Private local collector state: `collection_status.json`, `collection.log`, and `collect_verified.py` beneath the private-files directory in section 2. Historical process identifiers were training supervisor 1437870, finisher 1441612, and local collector 41891. Verify start-time/command identity before using any PID; they may now be stale.

## 8. Next actions when resuming

1. Read live server progress, error logs, final verification proof, and local collection status. After the restart, verify collector liveness independently.
2. Do not start duplicate training or bypass source/environment/marker checks. Preserve incomplete outputs for diagnosis if a unit failed.
3. If all 66 units and the independent gate passed, inspect per-unit maximum differences, table comparisons, and exact decision agreement; verify aggregate collection.
4. Update the publication report and completion checklist with actual evidence. Review any automatically collected files before a new commit or requested GitHub push.
5. Retain the scientific conclusion: stable incremental benefit and equivalence were not established. Emphasize robustness and selection instability without turning a post hoc decomposition into causal or clinical claims.
6. External/new-site validation, anatomical review, full-procedure uncertainty, and manuscript framing remain separate publication tasks.

## 9. DocStash archive status

The user requested this whole-chat Markdown archive on DocStash. After restart, the local Codex configuration contained the endpoint `https://mcp.docstash.ai`, but this task's tool catalog did not expose an authenticated DocStash tool. A direct unauthenticated initialization request returned HTTP 401 requiring an Authorization header. An attempted check for saved MCP authorization was rejected by automatic approval review as unauthorized credential access; that route was not retried.

This Markdown file is complete locally. **No successful DocStash upload has been verified.** Complete the upload using an authenticated DocStash connection and record its returned document URL/ID after read-back verification. Do not treat endpoint registration or local file creation as an uploaded archive.
