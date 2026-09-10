# Result versions and evidence map

| Version | People / protocol | Role in this portfolio | Evidence |
|---|---|---|---|
| Historical fMRI | 409; repeated 4-fold and separate historical LOSO | Earlier BrainLM/FC/CNN/Transformer experiments | [Archived overview](historical_README.md), [historical results](../../RESULTS.md#historical-409-subject-results) |
| Frozen fMRI v1 | 378; 5 repeats × 3 folds, 201/51/126 | Current representation and fuller-control story | [Verified tables](../../results/fmri_378), [source inventory](../../src/adhd_portfolio/frozen_v1/sources.json), [config](../../configs/fmri_v1.json) |
| Structural/functional fusion v1 | 350 / 302 / 375; QC sensitivity cohorts | Separate extension | [Fusion report](../structural_functional_fusion.md) |
| Structural fusion v2 | Separate currently running study | Not included in this release; no final claims | Requires separate completion, downstream stats and verification |

Do not apply a historical LOSO result to the newer tangent MLP. Do not compare 378-person and 350-person AUCs as paired model improvements. The current 0.7127 includes age/sex/site/motion information; image-only tangent MLP is 0.6453.

The old three top-level narrative documents are retained here for history, not as current entry points. Relative links in those copies have been adjusted to the archived or repository-root documents.
