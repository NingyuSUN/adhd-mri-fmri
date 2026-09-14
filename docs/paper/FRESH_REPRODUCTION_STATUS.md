# Fresh feature-level reproduction status

**VERIFIED on 2026-09-14: complete, with full feature-level reproduction acceptance passed.**

Source: the verified reproduction proof from the private SV002 workspace. The proof file modification time is 2026-09-11 07:39:31 UTC (16:39:31 Japan time); this is a file timestamp, not a separately recorded training-finish timestamp.

- 66/66 units: 45 CV and 21 LOSO; 17 model outputs per unit.
- All validation/test prediction comparisons: maximum absolute score difference 0.0.
- All 66 final fusion-weight comparisons identical.
- All 15 aggregate summary/metric table comparisons matched.
- Five statistical tables matched with maximum numeric difference 0.0; original decision reproduced exactly.
- Both pipeline and verification status: `verified_full_feature_level_reproduction`.

The aggregate [completion proof](../../results/paper_readiness_20260911/fresh_refit/verified_reproduction.json) was collected and its consistency assertions checked locally on 2026-09-14. No training or verifier was restarted during this check. All 34 allowlisted aggregate tables, figures and run metadata files have now been collected and checked against server SHA-256 values; see fresh_refit/server_artifact_manifest.json.

Scope: fresh fitting from frozen time-series and volume derivatives. This does not establish raw MRI preprocessing reproducibility, expert anatomical QC, causal interpretation, external validation, or clinical utility. The previous pending status and slide 53's 2026-09-11 snapshot predate final acceptance.
