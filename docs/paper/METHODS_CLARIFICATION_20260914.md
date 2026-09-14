# Methods clarification added after source review — 2026-09-14

This dated clarification supplements the frozen September 10 protocol/deviation record; it is not a retrospectively pre-registered amendment.

**VERIFIED from code:** LOSO holds out one site for testing. Within the other six sites, one stratified 85/15 split supplies fitting and validation data. Validation selects C, fusion alpha and early stopping. The selected models are used directly on the held-out site; they are not refit using the combined inner fitting and validation sets. Thus the fitting sample is about 85% of the available six-site sample, unlike protocol §5B's planned three-fold selection followed by full six-site refitting.

Paper wording: “LOSO used a single site-by-label-stratified inner holdout for tuning. Models fitted on the inner training subset were evaluated directly on the held-out site, without refitting on all remaining-site subjects. This deviated from the planned inner three-fold procedure and subsequent full-training-site refit.”

The held-out test site remains unused for selection in the inspected path. Omitted refitting changes the learning procedure and training sample size; its quantitative impact is unknown and cannot be assumed negligible or corrected by relabelling the result. A full-refit comparison would require a separately specified experiment. No such run has been performed here.

Sources: `reproduction/legacy/run_structural_fusion_v2.py:186` (run_fold), lines 195–227 (fit/selection), lines 229–236 (direct predictions); `docs/analysis_v2_protocol.md` §5B; `docs/analysis_v2_deviations.md` D1. Original “pre-registered” document headings are historical; prior exploration means they should not be presented as evidence of prospective registration without an actual registration record.
