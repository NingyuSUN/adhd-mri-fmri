# Final Project Report

## Project objective

This project asked whether deep learning applied to structural MRI and resting-state fMRI could predict ADHD in the multi-site ADHD-200 dataset. Its portfolio goal was to demonstrate an end-to-end medical-AI workflow; unseen-site generalization was evaluated as a demanding robustness test rather than treated as the only definition of project completion.

## What was completed

The study progressed from simple structural MRI CNNs to ROI-guided and ablation experiments, then to fMRI functional connectivity, graph representations, spectral features, a pretrained BrainLM representation, confound-aware robustness tests, and strict motion scrubbing.

The final evaluation was designed around a locked subject cohort and strict nested leave-one-site-out validation. Held-out sites were never used to fit scaling, feature selection, residualization, or model hyperparameters. Macro site AUC was chosen as the primary metric so that large sites could not dominate the conclusion.

## Main finding

The available data and tested methods do not support a reliable cross-site MRI/fMRI ADHD predictor.

In the portfolio-oriented repeated site-and-label-stratified experiment (`n=409`, four folds × five repeats), age + sex + motion/QC reached mean AUC 0.677 ± 0.058. FC plus frozen BrainLM reached 0.595 ± 0.031, FC ROI summary 0.583 ± 0.036, spectral features 0.570 ± 0.035, and frozen BrainLM alone 0.529 ± 0.043. This demonstrates above-chance within-dataset modeling for several image representations, but it also shows that confounds remain the strongest predictors.

On the locked fMRI cohort (`n=409`), the strongest result came from age, sex, and motion/QC variables (macro AUC 0.686). Motion/QC alone reached 0.664. In contrast, frozen BrainLM reached 0.512, FC plus BrainLM 0.501, spectral features 0.492, FC ROI summaries 0.477, and selected full-connectivity edges 0.430.

Adding BrainLM to the confound variables reduced macro AUC to 0.622. This is important: the imaging representation did not add stable information beyond the variables that describe demographics and data quality.

The structural results tell the same story. Pretrained Swin-T MRI reached strict LOSO OOF AUC 0.579 (95% CI 0.543–0.617), below the age + sex baseline of 0.619 (95% CI 0.584–0.656). The ROI-guided CNN reached LOSO OOF AUC 0.470. A less stringent single held-out split produced Swin-T AUC 0.774, but the age + sex + site baseline on the same split reached 0.781; strict site-held-out performance is therefore the relevant conclusion. No structural model established robust out-of-site anatomical signal.

## Robustness evidence

Several analyses tested whether a useful fMRI signal had been hidden by site shift or head motion:

1. A motion-restricted cohort retained a confound AUC of 0.657, while BrainLM fell to 0.406.
2. Training-fold-only residualization produced image-only AUCs of 0.461–0.490; adding residualized BrainLM to confounds reached 0.605, still below confounds alone.
3. Within-site validation produced 0.663 for confounds, 0.501 for spectral features, 0.459 for FC, and 0.443 for BrainLM.
4. Strict frame scrubbing on `n=246` subjects produced 0.506 for scrubbed FC, compared with 0.532 for original FC and 0.622 for confounds.
5. The paired bootstrap estimate for scrubbed minus original FC was -0.026, with a 95% interval from -0.149 to 0.072.
6. Spatial network aggregation did not improve the conclusion; scrubbed module features reached 0.441 and confounds plus scrubbed modules reached 0.541.

These checks consistently fail to show a reproducible image-derived gain.

7. A later QC-locked round retrained the structural, functional and non-imaging models together under one frozen protocol, on three prespecified cohorts (`primary` n=350, `warning_free` n=302, `include_holds` n=375) and the original 5×3 subject-level split identities (45 folds, 17 models each, all independently replay-verified). The non-imaging control reached mean AUC ≈ 0.71 in every cohort; adding functional imaging changed it by −0.013 (primary; 1 of 5 repeats positive) and adding structural volume on top changed it by −0.010 (primary; 0 of 5 positive). The only positive image-derived increment — adding structural to the image-only functional model — reached +0.017 in `primary` (5/5 repeats) but fell to +0.007 and +0.002 in the other two cohorts. Detail in `docs/structural_functional_fusion.md`.

## Decision about Transformer fine-tuning

Transformer fine-tuning was considered but is not required to finish the project. A prespecified gate required the frozen pretrained representation to be competitive with simpler baselines before spending substantially more compute. It did not pass that gate.

Fine-tuning a high-capacity model on this modest, heterogeneous cohort would increase overfitting risk and would not address the core problem revealed by the benchmark: confound signal is substantially stronger than transferable neuroimaging signal.

## Scientific conclusion

The correct conclusion is not that MRI and fMRI have no relationship with ADHD. It is narrower:

> Under the available ADHD-200 sample, preprocessing choices, representations, and strict cross-site evaluation, the tested MRI/fMRI models did not yield a stable, confound-independent subject-level ADHD predictor.

The project is therefore complete as a well-controlled negative or boundary result. It contributes a reproducible evaluation framework and demonstrates why apparent performance in multi-site neuroimaging must be compared with demographic, site, motion, and QC baselines.

## Planned v2 reanalysis and subsequent interpretation audit

The 66-unit v2 reanalysis did not confirm the pre-specified primary equivalence hypothesis. CV gave ΔAUC −0.011 with a corrected 90% interval [−0.040,+0.017]; primary-cohort LOSO gave +0.028 [+0.009,+0.046]. The latter supports a positive conditional contrast, not a demonstrated increment above +0.02. The other two QC cohorts gave negative LOSO contrasts.

The [2026-09-11 audit](docs/paper/STATISTICAL_INTERPRETATION.md) corrects the earlier explanations: NYU contributes 67.07% of primary within-site pairs, not approximately 40%; matched-subject analyses show the reversal is not explained chiefly by evaluation sample composition. The primary→warning_free total change −0.11319 decomposes into changed-pipeline −0.11889, evaluation-composition +0.00379, and site-weight +0.00191 contributions. A symmetric post hoc decomposition attributes much of the changed-pipeline term to the final fusion weight, conditional on saved predictions. This is evidence of pipeline sensitivity, not a proof that LOSO fails or that imaging contains no useful information.

Original protocols and machine-readable decisions are retained. New analyses are explicitly post hoc; external replication remains absent.

## Biologically-motivated feature subset vs. full automatic feature set (exploratory, 2026-09-18)

The original ROI-guided CNN's region choice (frontal cortex, cingulate, thalamus, caudate, putamen, pallidum, accumbens) corresponds to a real, literature-supported hypothesis — the fronto-striatal-thalamic circuit model of ADHD — recovered from project notebooks and matched to PubMed-verified citations in [`docs/paper/ROI_BIOLOGICAL_RATIONALE_AND_EVIDENCE.md`](docs/paper/ROI_BIOLOGICAL_RATIONALE_AND_EVIDENCE.md). That document also traces, for the first time, which atlas each later feature set actually uses (SynthSeg 2.0 for the 98 structural volume features; BrainLM's own Glasser HCP-MMP + subcortical + cerebellar A424 atlas for the 424 functional features), and uses that mapping to test the hypothesis directly: does restricting either feature set to the same literature-motivated regions do as well as the full automatic set, under an otherwise identical CV protocol?

- **Structural** (36 of 98 SynthSeg regions, ≈37%): mean CV AUC fell from 0.618 (LR) / 0.624 (MLP) on the full region set to 0.567 / 0.567 on the biological subset — consistently worse in all 5 of 5 CV repeats for both models.
- **Functional** (148 of 424 A424 nodes, ≈35%): mean CV AUC on the biological subset (0.621 LR / 0.625 MLP) was roughly on par with the full node set (0.615 / 0.621) — a small, inconsistent edge favoring the subset (3 of 5 repeats for both models), the opposite direction from structural.

Both comparisons reused the frozen, hash-verified splits, cohorts, and covariances and reproduced the published full-feature CV baselines almost exactly (internal validity check) before comparing arms. **These are single exploratory CV runs**, not run through this project's confirmatory statistical framework (no Nadeau–Bengio corrected interval, no TOST equivalence test, no LOSO) — the 5:0 and 3:2 counts are descriptive, not significance claims. The most defensible reading is not "the hypothesis is right for function and wrong for structure"; it is that narrowing a feature set to a literature-motivated region list changes structural and functional representations asymmetrically, for reasons partly diagnosed in the same document (diffuse, age-correlated structures such as white matter and ventricles appear to inflate the full structural model's apparent advantage; connectivity features already pass through an ANOVA edge-selection step that limits how much the full node set can add). Full design, diagnostics, and caveats are in the linked document.

## Intended use of outputs

The maintained analysis code and aggregate result tables are suitable for research benchmarking, methods development, and a thesis/project report. They are not suitable for clinical screening, diagnosis, treatment decisions, or individual risk communication.

## Reproducible artifacts

- Fresh fitting, statistical recomputation, and verification code in `reproduction/`
- Table and figure assembly code in `reporting/`
- Aggregate-only reviewer entrypoint and public-package validator in `tools/`
- Aggregate CSV tables, figures, and replay evidence in `results/`
- Evaluation and limitations in `RESULTS.md`, `REPRODUCIBILITY.md`, and `LIMITATIONS.md`
- Biological ROI/node rationale and exploratory subset-vs-full comparisons in [`docs/paper/ROI_BIOLOGICAL_RATIONALE_AND_EVIDENCE.md`](docs/paper/ROI_BIOLOGICAL_RATIONALE_AND_EVIDENCE.md) and `reproduction/exploratory/`

## If the research is extended later

The highest-value next step would not be another architecture sweep. It would be a larger, harmonized, acquisition-balanced dataset with better phenotyping and a truly independent external test cohort. Any future model should still be required to outperform a locked confound-only baseline and report site-wise uncertainty.
