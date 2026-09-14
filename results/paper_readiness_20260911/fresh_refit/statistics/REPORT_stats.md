# Analysis v2 — statistics (pre-registered)

Pre-registration: `docs/analysis_v2_protocol.md` sections 6-7. Bootstrap seed 20260910, 10000 resamples (site-stratified subject resampling; sites held fixed).

## Primary contrast P: `full_fusion_structural_mlp` - `full_functional_mlp`, cohort `primary`

- Mixed-site CV (Nadeau-Bengio, df=14): Δ = -0.0114, 90% CI [-0.0400, +0.0172] → **B4_inconclusive_underpowered**
- Strict LOSO (pair-weighted, subject bootstrap): Δ = +0.0275, 90% CI [+0.0095, +0.0463] → **B2_meaningful_increment**

### Verdict: FALSIFICATION TRIGGERED in at least one framework: audit before interpreting.

- CV: The data cannot establish equivalence: the 90% interval extends beyond +/-0.02. Point estimate reported; a small effect in the crossed direction cannot be excluded.
- LOSO: A methodologically meaningful positive increment cannot be ruled out and the estimate is positive; audit for leakage / confound imbalance before any positive claim.

### H2 (functional vs confound baseline, S1, primary): CV B4_inconclusive_underpowered (Δ -0.0068); LOSO B4_inconclusive_underpowered (Δ +0.0126)

## All contrasts — mixed-site CV (metric=auc)

| cohort | contrast | Δ mean | 90% CI (df14) | 90% CI (df2) | +/15 |
|---|---|---:|---|---|---:|
| primary | P | -0.0114 | [-0.0400, +0.0172] | [-0.0589, +0.0361] | 1 |
| primary | S1 | -0.0068 | [-0.0409, +0.0274] | [-0.0634, +0.0499] | 4 |
| primary | S2 | -0.0112 | [-0.0513, +0.0289] | [-0.0776, +0.0552] | 4 |
| primary | S3 | -0.0074 | [-0.0429, +0.0280] | [-0.0662, +0.0514] | 4 |
| primary | S4 | +0.0199 | [-0.0180, +0.0577] | [-0.0429, +0.0826] | 11 |
| primary | S5 | -0.0084 | [-0.0384, +0.0217] | [-0.0582, +0.0415] | 2 |
| primary | E1 | +0.0080 | [-0.0330, +0.0490] | [-0.0600, +0.0760] | 10 |
| warning_free | P | -0.0106 | [-0.0511, +0.0299] | [-0.0777, +0.0566] | 3 |
| warning_free | S1 | +0.0005 | [-0.0291, +0.0300] | [-0.0485, +0.0494] | 7 |
| warning_free | S2 | -0.0090 | [-0.0405, +0.0224] | [-0.0611, +0.0430] | 3 |
| warning_free | S3 | -0.0169 | [-0.0651, +0.0313] | [-0.0967, +0.0629] | 2 |
| warning_free | S4 | +0.0086 | [-0.0357, +0.0529] | [-0.0648, +0.0820] | 9 |
| warning_free | S5 | -0.0133 | [-0.0569, +0.0303] | [-0.0855, +0.0590] | 4 |
| warning_free | E1 | +0.0141 | [-0.0237, +0.0520] | [-0.0486, +0.0769] | 9 |
| include_holds | P | -0.0025 | [-0.0222, +0.0173] | [-0.0352, +0.0303] | 4 |
| include_holds | S1 | -0.0006 | [-0.0281, +0.0268] | [-0.0461, +0.0448] | 7 |
| include_holds | S2 | -0.0095 | [-0.0454, +0.0264] | [-0.0691, +0.0500] | 3 |
| include_holds | S3 | -0.0132 | [-0.0495, +0.0231] | [-0.0734, +0.0470] | 2 |
| include_holds | S4 | +0.0056 | [-0.0419, +0.0532] | [-0.0732, +0.0845] | 9 |
| include_holds | S5 | -0.0095 | [-0.0430, +0.0241] | [-0.0651, +0.0461] | 2 |
| include_holds | E1 | +0.0225 | [-0.0251, +0.0701] | [-0.0564, +0.1014] | 11 |

## All contrasts — strict LOSO (pair-weighted AUC)

| cohort | contrast | Δ point | 90% CI (boot) | Δ drop-small |
|---|---|---:|---|---:|
| primary | P | +0.0275 | [+0.0095, +0.0463] | +0.0297 |
| primary | S1 | +0.0126 | [-0.0331, +0.0615] | +0.0126 |
| primary | S2 | +0.0077 | [-0.0017, +0.0179] | +0.0095 |
| primary | S3 | +0.0083 | [-0.0012, +0.0186] | +0.0102 |
| primary | S4 | +0.0121 | [-0.0161, +0.0405] | +0.0134 |
| primary | S5 | +0.0114 | [-0.0046, +0.0284] | +0.0119 |
| primary | E1 | -0.0282 | [-0.0822, +0.0248] | -0.0276 |
| warning_free | P | -0.0857 | [-0.1607, -0.0103] | -0.0852 |
| warning_free | S1 | -0.0010 | [-0.0078, +0.0058] | -0.0014 |
| warning_free | S2 | -0.0390 | [-0.0978, +0.0200] | -0.0384 |
| warning_free | S3 | -0.0358 | [-0.0945, +0.0230] | -0.0353 |
| warning_free | S4 | -0.0086 | [-0.0906, +0.0751] | -0.0074 |
| warning_free | S5 | -0.0446 | [-0.1011, +0.0116] | -0.0439 |
| warning_free | E1 | +0.0102 | [-0.0263, +0.0461] | +0.0107 |
| include_holds | P | -0.0429 | [-0.0739, -0.0113] | -0.0428 |
| include_holds | S1 | +0.0254 | [+0.0040, +0.0484] | +0.0257 |
| include_holds | S2 | -0.0026 | [-0.0060, +0.0006] | -0.0026 |
| include_holds | S3 | -0.0031 | [-0.0065, +0.0002] | -0.0029 |
| include_holds | S4 | -0.0037 | [-0.0264, +0.0199] | -0.0031 |
| include_holds | S5 | -0.0279 | [-0.0516, -0.0049] | -0.0281 |
| include_holds | E1 | +0.0221 | [-0.0021, +0.0464] | +0.0227 |

## Notes

- Δ = candidate − reference. Positive = imaging helps.
- CV interval: Nadeau & Bengio (2003) corrected resampled t; correction = 1/15 + 0.5; df = r·k−1 = 14 (df = k−1 = 2 shown as conservative sensitivity). Bouckaert & Frank (2004) for df.
- LOSO interval: site-stratified subject bootstrap (7 sites held fixed). Cluster bootstrap over 7 sites was rejected in review as invalid. Per-site Δ and within-site CIs in `loso_per_site_deltas.csv` (forest plot F1).
- Repeat range / positive-fold counts are descriptive, not tests.
- No family-wise correction across the 7 contrasts × 3 cohorts: they are same-direction consistency checks, and all-≤0 observed Δ means multiplicity would inflate false positives, not false nulls. Any Δ CI excluding 0 on the positive side is flagged.