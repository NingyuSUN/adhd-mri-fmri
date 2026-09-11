# Analysis v2 — confirmatory round (pre-registration)

**Status: FINALIZED 2026-09-10 after Gemini 3.1 Pro methods/stats review
(`coordination/gemini/v2protocol_review_20260910/REVIEW.md`). 4 must-fix items
applied (decision tree, LOSO primary metric, bootstrap scheme, NB formula).
No code written yet.**
Builds on the frozen `structural_fusion_locked_20260909` round.

---

## 0. Purpose

The 20260909 round showed that adding functional and/or structural MRI to a
non-imaging confound baseline does not raise AUC (paired Δ negative or ~0 in all
three QC cohorts). That round has three weaknesses a reviewer will flag:

- **W1** MLP ensemble seeds are `1200/2200/3200 + fold` — no repeat index, so the
  5 repeats reuse identical initializations for a given fold → repeat variance is
  an underestimate → any downstream interval on the paired Δ is too tight.
- **W2** The increment is reported as `mean_delta` + "positive repeats /5". That is
  neither a confidence interval nor a hypothesis test, and there is no equivalence
  test — so "no increment" is not distinguished from "underpowered".
- **W3** The strongest evidence in the wider project (strict nested LOSO collapse of
  imaging models) was produced on the earlier fMRI-only benchmark. The 20260909
  structural + functional + fusion round used mixed-site 5×3 CV only. The final
  fusion models were never tested for cross-site transport.

v2 fixes W1–W3 in a single pre-registered confirmatory round and adds a formal
equivalence test, calibration analysis, and figures. **It does not chase a higher
score and does not add new architectures or representations.**

## 1. Hypotheses

Primary (H1): On top of a non-imaging confound baseline plus functional imaging,
adding structural MRI provides **no methodologically meaningful increment** in
AUC, defined as the paired ΔAUC 90% interval lying entirely within
[−0.02, +0.02].

Secondary:
- H2: functional imaging adds no meaningful increment over the confound baseline
  alone (same equivalence definition).
- H3: the H1/H2 conclusions hold under strict leave-one-site-out (LOSO) as well as
  mixed-site CV.
- H4 (descriptive): image-model probability outputs are not calibrated to
  diagnostic risk.

## 2. Data — frozen, identical to 20260909 (no change)

- QC lock `runs/structural_qc_locked_20260909/qc_lock.json`
  (sha256 `e03ad883…8ddc4`). 378 reviewed = 302 coarse + 48 warning + 25 HOLD +
  3 failure.
- Cohorts: `primary` n=350, `warning_free` n=302, `include_holds` n=375.
  Prespecified sensitivity design; never selected by score.
- Structural: 98 region/TIV volume fractions (`volumes_NOT_TRAINING_READY.npz`,
  sha256 `dceb3116…9c3`). Not cortical thickness.
- Functional: A424 within-subject Ledoit–Wolf covariances → tangent space,
  reference point fit on training data only. Covariance cache reused
  (`covariances.npy`, within-person only).
- Confounds: site, head-motion summaries, age, sex (+ TIV in the `*_tiv_*`
  models) — from `runs/demographic_increment_20260908_locked_v2/{cohort,splits}.csv`
  (shas `0f4386b2…`, `e07e6a69…`). **Pre-registered statement:** this is a
  re-analysis of existing data; the non-imaging models use every systematically
  standardized acquisition and demographic variable available in the ADHD-200
  derivatives. Scanner-hardware detail, medication-at-scan, comorbidity and IQ
  are not uniformly available and are out of scope; their absence is a
  limitation, not a modeling choice.
- Site composition (all cohorts, both classes present at every site):
  NYU ~139, KKI 82, Peking_1 ~49, OHSU ~32, NeuroIMAGE ~28, Peking_2 14,
  Peking_3 6.

## 3. What changes vs 20260909

| # | Change | Reason |
|---|---|---|
| C1 | MLP ensemble seed = `base + fold*10 + repeat` (was `base + fold`) | W1 — independent repeat trajectories |
| C2 | **Pre-registered primary contrast is symmetric:** `full_fusion_structural_mlp − full_functional_mlp` (both add an MLP-derived modality). The `full_fusion_mlp` (adds structural **LR**) contrast is demoted to secondary. | Reviewer critique: the 20260909 primary contrast handicapped structure by adding it as LR onto an MLP functional model |
| C3 | Add a **strict nested LOSO** evaluation of the contrast-relevant models, alongside the mixed-site CV | W3 |
| C4 | Formal statistics: Nadeau–Bengio corrected variance (CV) + site-level paired bootstrap (LOSO) + pre-registered TOST | W2 |
| C5 | Calibration analysis (reliability curve + ECE) on v2 predictions | H4 evidence |
| C6 | Figures: site/cohort ΔAUC forest plot; confound-vs-imaging bar | portfolio + `figures/` is currently empty |

**Not changed:** QC lock, cohort definitions, feature definitions, C grid
{0.01,0.1,1,10}, α grid {0,0.25,0.5,0.75,1}, MLP architecture 64/16 GELU
dropout 0.4/0.3 patience 12 epochs 80, "validation-only" selection principle,
tangent geometry params, tie-break rules, covariance cache. New frozen
`protocol_v2.json` with its own code/input hashes; new run directory
`runs/structural_fusion_v2_YYYYMMDD`. The 20260909 run is untouched.

## 4. Models and contrasts

Same 17 model/fusion outputs as 20260909 (`structural_lr`, `structural_tiv_lr`,
`tiv_lr`, `full_covariates_lr`, `full_covariates_tiv_lr`, `tangent_lr`,
`structural_mlp`, `tangent_mlp`, `image_fusion_lr`, `image_fusion_mlp`,
`full_functional_lr`, `full_functional_mlp`, `full_functional_tiv_mlp`,
`full_fusion_lr`, `full_fusion_mlp`, `full_fusion_tiv_mlp`,
`full_fusion_structural_mlp`).

Pre-registered contrasts (candidate − reference):

| # | Contrast | Role |
|---|---|---|
| P | `full_fusion_structural_mlp` − `full_functional_mlp` | **PRIMARY** (H1) |
| S1 | `full_functional_mlp` − `full_covariates_lr` | secondary (H2) |
| S2 | `full_fusion_mlp` − `full_functional_mlp` | secondary (adds structural LR) |
| S3 | `full_fusion_lr` − `full_functional_lr` | secondary (all-LR path) |
| S4 | `image_fusion_mlp` − `tangent_mlp` | secondary (image-only: +structural) |
| S5 | `full_fusion_tiv_mlp` − `full_functional_tiv_mlp` | secondary (TIV path) |
| E1 | `structural_mlp` − `structural_lr` | descriptive (does structure need non-linearity) |

## 5. Evaluation frameworks

### 5A. Repeated mixed-site CV (re-run of 20260909 with C1)
- Same saved 5-repeat × 3-fold subject-level split identities, filtered by QC
  cohort. Preprocessing, feature selection, C/α/early-stopping fit on the
  training fold only. 45 folds × 17 models per cohort.
- Primary metric: mean of fold AUC, then mean across the 5 repeats.
- Secondary: within-site pair-weighted AUC (`conditional_auc`).

### 5B. Strict nested LOSO (new)
- Outer loop: 7 folds, each holds out one acquisition site.
- Inner selection on the 6 training sites: **3-fold, jointly stratified by site
  and label**, used only to pick C, α and the MLP early-stopping epoch. After
  selection, refit on all 6 training sites; predict the held-out site once.
  (Rationale for inner k-fold rather than inner-LOSO: ~6× cheaper, and the inner
  set only chooses hyperparameters; the reviewer-relevant test is the outer
  held-out site.)
- MLP seeds for LOSO: `base + outer_site_index` (repeat index not applicable);
  3-seed equal-weight ensemble as before.
- Metrics (revised per review — an unweighted 7-site mean is variance-dominated
  by the n=6 and n=14 sites):
  - **Primary LOSO metric: within-site pair-weighted AUC** (`conditional_auc`) —
    pair-count-weighted mean of the per-site held-out AUCs; only within-site
    positive–negative pairs contribute, so larger and more class-balanced sites
    get more weight automatically.
  - Secondary: unweighted macro AUC (mean of the 7 site AUCs); pooled OOF AUC.
  - Sensitivity: drop sites with n < 20 (Peking_2 n=14, Peking_3 n=6); recompute
    both pair-weighted and macro over the remaining 5 sites.
- Run for all three cohorts.

## 6. Statistical analysis plan

### 6A. Mixed-site CV deltas — Nadeau–Bengio corrected variance
For each contrast, per cohort:
- Δ_ij = AUC(candidate) − AUC(reference) at repeat i, fold j (i=1..5, j=1..3).
- Point estimate = mean(Δ_ij).
- Variance: Nadeau–Bengio correction for repeated k-fold CV. Exact expression to
  implement (k=3 folds, r=5 repeats; per fold n_test/n_train = (1/3)/(2/3) = 0.5):
  ```
  correction = 1/(r*k) + n_test/n_train = 1/15 + 0.5
  var_corrected = correction * var(Δ_ij, ddof=1)
  se_corrected  = sqrt(var_corrected)
  df = r*k - 1 = 14
  ci_90 = mean(Δ) ± t.ppf(0.95, df) * se_corrected
  ```
  Citations: Nadeau & Bengio 2003, *Machine Learning* 52(3):239–281 (the
  corrected-resampled-t estimator); Bouckaert & Frank 2004, *PAKDD* (df = r·k−1
  for repeated k-fold). *(needs-verification: some authors use df = k−1; we
  pre-register df = r·k−1 = 14 and will also report the k−1 = 2 interval as a
  conservative sensitivity.)*

### 6B. LOSO deltas — site-stratified subject bootstrap (revised: no cluster bootstrap)
Cluster/cluster-resampling bootstrap over only 7 sites is invalid (needs ~30+
clusters for usable coverage; 7 clusters → severely anti-conservative SE). Instead:
- For each contrast, per cohort, the point estimate of the summary Δ is on the
  **pair-weighted** metric (5B primary).
- 10,000 bootstrap resamples: **hold the 7 sites fixed**; within each site resample
  its subjects with replacement (site-stratified subject bootstrap); recompute the
  held-out prediction metric and the pair-weighted summary Δ each time.
- Report the 90% percentile interval of the summary Δ.
- Forest plot: per-site ΔAUC point estimate + its own within-site subject
  bootstrap 95% interval, to show cross-site heterogeneity honestly rather than
  hide it in a summary.
- The n=6 / n=14 site intervals will be very wide by construction — that is the
  correct, honest representation.

### 6C. Pre-registered equivalence test (TOST)
- Equivalence margin **Δ_eq = 0.02 AUC**. Rationale to state in the write-up:
  0.02 is below the fold-to-fold and site-to-site AUC noise observed in this
  project (repeat range spans ≈0.03–0.05; LOSO site AUCs span far more), and
  below any threshold that would change a screening decision; it is a
  *methodological* materiality bound, explicitly **not** a clinical one.
- Test: two one-sided tests at α = 0.05. This is exactly equivalent to checking
  whether the **90%** (= 1 − 2α) interval for Δ lies entirely within [−0.02, +0.02]
  — the 6A t-interval for framework 5A, the 6B percentile interval for 5B.
  (Percentile-interval TOST is asymptotically valid **only** because 6B was
  revised to site-stratified subject bootstrap; it would not be valid for the
  discarded 7-cluster bootstrap.)
- Applied to the PRIMARY contrast P in both frameworks (5A and 5B) and,
  descriptively, to secondary S1. Decision branches: section 7.

### 6D. Multiple comparisons
7 contrasts × 3 cohorts × 2 frameworks. The primary claim rests on contrast P in
the `primary` cohort under both frameworks. Secondary contrasts and the other two
cohorts are reported with a note that no family-wise correction is applied
because (i) they are consistency checks in the same direction, not independent
discovery tests, and (ii) all observed Δ are ≤ 0 — a scenario where multiplicity
inflates false *positives*, not false nulls. If any secondary Δ interval excludes
0 on the positive side, it is flagged and interpreted cautiously.

## 7. Pre-registered decision rules (primary contrast P, `primary` cohort)

Let [L, U] be the 90% interval for the primary contrast Δ (6A for framework 5A,
6B for framework 5B). The four branches below are **mutually exclusive and
exhaustive** (revised per review — the earlier draft's "bounded null" and
"increment detected" branches overlapped when the interval sat inside (0, 0.02]):

| Branch | Condition on [L, U] | Conclusion wording |
|---|---|---|
| **B1 — bounded null (confirm)** | −0.02 ≤ L and U ≤ +0.02 | "Adding structural MRI to the confound + functional pipeline does not produce a methodologically meaningful AUC increment: the paired Δ is equivalent to zero to within ±0.02 AUC." (Applies even if the whole interval is slightly above 0 but ≤ 0.02 — that is still no meaningful increment.) |
| **B2 — meaningful increment (not expected)** | L > 0 **and** U > +0.02 | "A methodologically meaningful positive increment cannot be ruled out and the estimate is positive." Re-examine for leakage / confound imbalance before any positive claim; do not report as a biomarker without external replication. |
| **B3 — meaningful decrement (not expected)** | U < −0.02 | "Adding imaging meaningfully lowered AUC." Investigate (overfitting of the added modality, α-selection instability). |
| **B4 — inconclusive / underpowered** | interval straddles a margin (L < −0.02 ≤ U ≤ +0.02, or −0.02 ≤ L ≤ +0.02 < U, or L < −0.02 and U > +0.02) | "The data cannot establish equivalence: the 90% interval [L, U] extends beyond ±0.02. The point estimate is [value]. We cannot exclude an effect up to \|bound\| AUC in the direction(s) the interval crosses." State the exact bound(s). |

The **primary claim** is confirmed only if branch **B1 holds in both framework
5A and framework 5B** for the `primary` cohort. If 5A gives B1 but 5B gives B4
(or vice versa), the write-up reports "bounded null within-dataset; cross-site
transport underpowered" (or the reverse) — no unqualified equivalence claim.

Same four-branch rule applied descriptively to H2 (contrast S1) and to the
`warning_free` / `include_holds` cohorts; these are consistency checks, not
independent confirmations.

## 8. Calibration (H4)
- Pooled v2 test-fold predictions per model, per cohort.
- Reliability curve (10 equal-count bins) + Expected Calibration Error + Brier +
  Brier skill score vs prevalence.
- Report for `full_covariates_lr`, `full_functional_mlp`,
  `full_fusion_structural_mlp`, `image_fusion_mlp`.
- Pre-registered statement regardless of result: outputs are class-weighted and
  uncalibrated and must not be read as individual risk.

## 9. Figures
- F1: forest plot — per-site ΔAUC (primary contrast, LOSO) with bootstrap CIs,
  one panel per cohort.
- F2: bar chart — mean AUC of confound baseline vs each imaging/fusion model,
  `primary` cohort, mixed-site CV, with repeat range whiskers.
- F3: reliability curves, 4 models overlaid, `primary` cohort.

## 10. Verification
Same as 20260909: per-fold `complete.json` with file hashes + `protocol_v2` sha;
independent replay of all model outputs against saved predictions;
`verification.json` status `verified`; run + verify end-to-end on one host.

## 11. Deviations
Any deviation from this document after the run starts is logged in
`runs/structural_fusion_v2_*/DEVIATIONS.md` with timestamp and reason. The
primary contrast, margin, and decision rules are fixed once the run starts.

## 12. Compute
- 5A re-run: ~10 h CPU on SV002 (like 20260909).
- 5B LOSO: 7 outer × 3 cohorts, inner 3-fold selection; estimate ~6–10 h CPU.
- Stats / calibration / figures: local, minutes.
- Total wall-clock ~1 day of unattended server time + ~2–3 days analysis/writeup.

## 13. Reviewer questions — resolved (Gemini 3.1 Pro, 2026-09-10)

Full review: `coordination/gemini/v2protocol_review_20260910/REVIEW.md`.

1. **Inner 3-fold (site+label stratified) for LOSO hyperparameter selection** —
   accepted, and preferred over nested inner-LOSO (an inner held-out n=6 site
   would make C/α/epoch selection wildly unstable). Kept as written in 5B.
2. **Δ_eq = 0.02** — accepted as a prior methodological-materiality bound.
   Retrospective power / minimal-detectable-effect calculation explicitly
   rejected (statistical circularity). Kept.
3. **NB formula** — provided and written into 6A: correction = 1/15 + 0.5,
   var = correction·var(Δ, ddof=1), df = r·k−1 = 14, t.ppf(0.95, 14); cite
   Nadeau & Bengio 2003 + Bouckaert & Frank 2004. Also report the df = k−1
   conservative interval as sensitivity.
4. **Primary contrast** — P only, NOT co-primary with S2. Co-primary would force
   an α-split / multiplicity correction and lose power; P (symmetric MLP fusion)
   most directly answers the "structure was handicapped" critique. Kept.
5. **Cluster bootstrap over 7 sites** — rejected as invalid (needs ~30+ clusters;
   7 clusters → anti-conservative SE). Replaced in 6B with site-stratified
   subject bootstrap for the summary Δ + per-site forest plot with within-site
   subject-bootstrap CIs.
6. **Additional confounds** — current set (age, sex, site, motion, TIV) is
   accepted as strong. A strict reviewer might want scanner-hardware detail and
   medication/comorbidity at enrollment; these are not uniformly available in the
   ADHD-200 derivatives. Section 2 now carries the pre-registered statement that
   the non-imaging models exhaust the systematically standardized variables and
   the rest is an acknowledged limitation.

### Must-fix items from the review — all applied
1. Decision tree rewritten to 4 mutually-exclusive exhaustive branches (§7).
2. LOSO primary metric changed macro AUC → within-site pair-weighted AUC (§5B).
3. Cluster bootstrap removed; site-stratified subject bootstrap (§6B).
4. Exact NB formula + df + citations written into §6A.

## 14. Falsification conditions

- Any pre-registered contrast Δ 90% interval that lies entirely above +0.02
  (branch B2) in the `primary` cohort under either framework → the "no
  incremental value" conclusion is falsified for that contrast; report the
  positive finding and audit for leakage before interpreting.
- `full_covariates_lr` failing to exceed 0.60 AUC in framework 5A `primary` →
  the confound baseline itself is broken; halt and debug before trusting any
  contrast.
- Replay verification (§10) failing on any fold → no results released.
- Inner-selection choosing the boundary of the C or α grid in >50% of folds for
  a contrast-relevant model → grid too narrow; report as a limitation, do not
  silently widen.
