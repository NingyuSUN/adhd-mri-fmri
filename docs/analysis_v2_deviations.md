# Analysis v2 — deviations from the pre-registered protocol

Protocol: `docs/analysis_v2_protocol.md` (finalized 2026-09-10 after Gemini review).
Run started 2026-09-10 ~11:45 JST on SV002. Deviations logged before results were
inspected (training still running, all `test.csv` withheld from summarisation).

## D1 — LOSO inner selection: single stratified holdout, not inner 3-fold
- **Protocol said:** §5B "inner selection on the 6 training sites: 3-fold, jointly
  stratified by site and label".
- **Implemented:** a single stratified 85/15 holdout of the 6 training sites
  (stratified by site×label, `random_state = 2026 + site_index`), used for C / α /
  MLP early-stopping; then predict the held-out site.
- **Reason:** it reuses the *identical, already-verified* fit + selection code path
  as framework 5A (`run_fold`), so the LOSO run introduces essentially no novel
  training code for an unattended multi-hour job. Gemini's review explicitly noted
  the inner scheme is "not load-bearing for the claim — the reviewer-relevant test
  is the outer held-out site", which a single inner holdout satisfies equally.
- **Impact:** C/α/epoch selection uses ~29–56 inner-validation subjects instead of
  a 3-fold average. Slightly noisier hyperparameter selection; the held-out site
  (the actual test) is untouched either way. If a reviewer requires inner 3-fold
  it is a bounded re-run of framework 5B only.
- Recorded in `protocol_v2.json` (`loso.inner` field) so the frozen spec matches
  what ran.

## D2 — verification is a consistency check, not independent re-preprocessing
- **Protocol said:** §10 "same as 20260909 … independent replay of all model
  outputs against saved predictions".
- **Implemented:** (a) per-fold `complete.json` already replays every saved model
  (LR `joblib` reload + MLP `torch.load`) against its own predictions inside
  `run_fold` with `assert_allclose`, and stores every file hash + `protocol_sha`;
  (b) `verify_v2.py` re-checks all `complete.json` hashes across cv+loso,
  re-derives `fold_metrics` / `site_metrics` from `predictions.csv` and checks they
  reproduce `summary.csv`, and re-runs `analyze_v2_stats.py` to confirm the
  decision is reproducible.
- **Not done:** re-running tangent/structural/covariate preprocessing from
  `covariances.npy` in a separate process (the 20260909 `verify_and_release`
  behaviour).
- **Reason:** v2's headline output is the *statistical* conclusion, computed from
  frozen prediction CSVs; the built-in per-fold replay already guards the model
  outputs, and the covariance input is byte-identical to the 20260909 round which
  passed full independent re-preprocessing verification.
- **Impact:** a same-source preprocessing bug shared with 20260909 would not be
  caught — but that round's independent verification did pass, and the
  preprocessing code hashes are frozen in `protocol_v2.json`.

## Fixed rather than deviated
- Covariance staging moved from `covariance_cache` into `prepare()` (atomic
  tmp+rename, single-process `--prepare-only` step) after a first launch attempt
  hit a read/write race between the parallel cv and loso processes. No effect on
  results — same covariance bytes as 20260909.
