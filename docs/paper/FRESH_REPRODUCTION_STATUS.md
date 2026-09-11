# Fresh feature-level reproduction status

Status snapshot: 2026-09-11. **Running; not yet a completed 66-unit reproduction.**

- First fresh unit: `cv / primary / repeat1_fold1`, 17 outputs, 765 validation prediction rows and 2,006 test prediction rows. Maximum absolute prediction difference from the original: **0.0** for both sets. Selected fusion weights identical. Runtime approximately 981 seconds.
- Full execution: 45 CV + 21 LOSO units, six workers. The completed trial is reused after verification. Remaining units are still being fitted.
- All 378 within-person covariances were recomputed from time series and are byte-identical to the original reference. The second invocation reused this new cache.
- Independent preflight validated 910 reference records, all 12 cohort/split metadata files, the raw time-series checksum, covariance checksum and original unit manifests.
- Clean-environment statistical recomputation is complete separately: five original tables, exact decision and three figures.

The existing training runs under `<REPRO_DIR>/fresh_v2` on the analysis server. A separate finisher waits for that process to exit, then verifies all unit artifacts, exact roles, 17-model validation/test comparisons, fusion weights, aggregate summaries, statistics and figures. Only successful final verification produces `verified_reproduction.json`. Any failure is written to `pipeline_status.json` / `verification_status.json`. No second training run is started.

An attached collection process copies **aggregate** proof/tables/figures to `results/paper_readiness_20260911/fresh_refit/` only after successful verification and then replaces this status page with exact completion evidence. A training or connection failure leaves this page pending; absence of a collected final proof is not success. The private collector state/log is stored outside this repository.

This reproduces fitting from frozen time-series/volume derivatives. Raw MRI preprocessing, anatomical re-review and external validation remain outside the claim. No GitHub push has been made for this work.
