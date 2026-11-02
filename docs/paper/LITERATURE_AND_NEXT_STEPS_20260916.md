# ADHD project: comparison with published studies and follow-up plan (2026-09-16)

**Status labels:** VERIFIED = checked; INFERRED = inference supported by evidence; PROPOSED = recommended but not carried out; NOT VERIFIED = not yet checked.

## Conclusion

**Recommended order: check the existing intervals → document the imaging sources and methods → run one narrowly scoped stability experiment → then assess external data.**

The question worth pursuing is whether structural and functional imaging add stable predictive value beyond age, sex, site and head motion. If any such gain changes with quality control and the validation scheme, which pipeline choices are associated with that change?

This is a methodological re-analysis direction (PROPOSED) with some research value (INFERRED). This document is not a full novelty review and does not guarantee publication. A negative result, exact reproduction and passing engineering tests do not by themselves show that a scientific conclusion is adequate.

## Scope and search method

**Existing work and the boundary of this document:**

- Reproduction, QC decomposition and the tied-score counterexample are existing analyses.
- This document does not retrain any model and does not recompute anything from subject-level predictions.

**Search approach:**

- Candidate papers were found through semantic search, a citation database and PubMed.
- Key conclusions were checked against the publishers' full texts.

**Comparison scope:**

- A targeted comparison of six published original studies, covering ADHD-200 baselines, fusion, site bias, a large-sample structural model, application to a new sample and connectome methods.
- One 2025 multimodal paper is listed only as a candidate because its full text could not be obtained; it was not used to assess any specific design.
- This is a question-driven literature comparison, not a systematic review or meta-analysis, and it does not cover the whole field. Papers were chosen for how well they illustrate baseline design, data splitting, processing provenance and validation boundaries, not ranked by accuracy or publication year.

### Search strings

Semantic search question: How have published ADHD-200 studies compared structural MRI and resting-state fMRI multimodal prediction against demographic confound baselines, using held-out sites or independent test sets, and what do they report about generalizability and quality-control sensitivity?

Initial citation-database search: `ADHD AND (multisite OR multi-site) AND (classification OR prediction)`, followed by lookups of specific DOIs. Unrelated records and preprints from the broad search were not treated as evidence from formal publications.

Initial PubMed search:
- Terms: ADHD/attention deficit hyperactivity + MRI/neuroimaging + multisite/multi-site/external validation + classification/prediction, restricted to titles and abstracts, sorted by relevance, top 10 records.
- This narrow search returned only 3 records and cannot be used to estimate the number of papers in the field.
- The formal records of candidate papers were also checked by PMID, including 36651494 and 36172513. Metadata alone cannot support methodological conclusions.

**What was checked:**
- The full texts of ENIGMA 2021 and van Rooij 2022 were read.
- Some PMC pages were inaccessible, so the publishers' full texts were read instead.
- The full text of MATNet could not be obtained.

## What comparable studies did and what can be learned

### 1. Brown et al., 2012: set up a strong baseline of basic information first

**What they did:**
- Built models from age, sex, IQ, site and similar information and compared them with imaging methods.
- The competition held back subjects with unreleased labels; a later analysis covered 171 test participants with released labels.
- The personal-information model performed strongly.

**What to adopt:** keep a strong baseline of basic information. The task, sample and accuracy metric differ, so its results cannot be compared directly with this project's AUC.

[Paper: ADHD-200 Global Competition](https://www.frontiersin.org/journals/systems-neuroscience/articles/10.3389/fnsys.2012.00069/full)

### 2. Bohland et al., 2012: imaging fusion can also add predictive ability

**What they did:**
- Compared personal information, anatomy, functional networks and their combinations, reporting results on 168 held-out test participants.
- The all-features combination reached a test AUC of about 0.78, against about 0.72 for personal information.
- The paper documents segmentation, manual quality checks and the functional processing pipeline.

**What to adopt:** this comparison matrix and way of reporting provenance. Its design is not the same as LOSO in which every test site is unseen, and it does not imply that this project should reach the same score.

[Paper: Network, Anatomical, and Non-Imaging Measures](https://www.frontiersin.org/journals/systems-neuroscience/articles/10.3389/fnsys.2012.00078/full)

### 3. Olivetti et al., 2012: the splitting scheme can itself be the research question

**What they did:**
- Compared an ordinary split, subject-level separation and leave-one-site-out validation.
- Checked repeat scans and site differences and reported confusion matrices.

**What to adopt:** explain generalization differences with concrete comparisons. Mixed-site cross-validation is not wrong in general; it answers a different question from "predict a new site". This paper also cannot directly explain the QC reversal seen in this project.

[Paper: ADHD diagnosis from multiple data sources with batch effects](https://www.frontiersin.org/journals/systems-neuroscience/articles/10.3389/fnsys.2012.00070/full)

### 4. Zhang-James et al., 2021: a large sample also reports only limited predictive ability

**What they did:**
- 4,183 people from 35 sites; after excluding those missing more than half of the features, 4,042 were analysed.
- Described the FreeSurfer pipeline and 151 features.
- Split the data roughly 70/15/15 into training, validation and test sets, stratifying by site; sites with only one class were placed in the test set separately.
- The children's imaging model reached a test AUC of about 0.64.

**What to adopt:** how methods and uncertainty are reported. Note that this is not LOSO in which each site is held out in turn.

[Paper: Evidence for similar structural brain anomalies](https://www.nature.com/articles/s41398-021-01201-4)

### 5. van Rooij et al., 2022: a new sample must match the validation question

**What they did:**
- Applied an existing ENIGMA model to 133 ADHD patients from two centres, reusing the training data's transformations and visually checking the segmentations.
- Also studied the relationship between comorbidity and the scores.

**Caution:**
- A cases-only cohort cannot estimate specificity for ADHD versus healthy participants and cannot yield a binary-classification AUC.
- The mean score of 0.57 reported in the paper is not 57% classification accuracy.

**What to adopt:** the practice of fixing the model and the QC. But not every application to a new sample can be called a full diagnostic external validation.

[Paper: Structural brain morphometry as classifier and predictor](https://www.frontiersin.org/journals/psychiatry/articles/10.3389/fpsyt.2022.869627/full)

### 6. Rosenblatt et al., 2024: pipeline reliability can itself be a research contribution

**What they did:** compared several leakage scenarios — feature selection, covariate handling and subject dependence — on four connectome datasets. Letting test information into feature selection, or letting the same subject appear in both training and test sets, clearly changed performance.

**What to adopt:** set up testable comparisons aimed at pipeline differences. It is not an ADHD binary-classification performance study, and it cannot show that this project has the same leakage.

[Paper: Data leakage inflates prediction performance](https://www.nature.com/articles/s41467-024-46150-w)

### Verification boundary for the 2025 candidate paper

The abstract of MATNet (Journal of Electronic Imaging, DOI `10.1117/1.jei.34.4.043008`) reports high performance across several sites. Because the full text of the methods could not be obtained, none of the following were checked:
- how the data were split and how hyperparameters were selected;
- whether whole sites were held out;
- whether covariate baselines were used and how QC was done.

It is therefore listed only as a candidate for later full-text review. No change of model is recommended on the basis of the abstract alone, and no criticism of its design is made.

[Paper DOI](https://doi.org/10.1117/1.jei.34.4.043008)

## Shared lessons for this project

**INFERRED:** each research question should be paired with the evidence that answers it, rather than copying high-scoring models.

| Question | Comparison needed | What cannot replace it |
|---|---|---|
| Does imaging add value? | A basic-information model and a model with imaging added, on the same test participants and the same split | Comparing top scores across papers or cohorts |
| Can it predict new participants from similar sources? | Subject-level separated testing, or appropriate cross-validation | Splitting one person's slices or time windows |
| Does it still work at another hospital? | Whole-site held-out testing, with per-site results | Only random mixed-site splits |
| Does it generalize to an independent cohort? | A new cohort with a matching definition, plus a validation plan fixed in advance | Repeatedly re-splitting the old data; using a cases-only sample as a case–control evaluation |
| Is the meaning of the features clear? | Source, processing version, atlas, units and image QC | Correct dimensions or identical hashes |
| Why are the results unstable? | Prespecified pipeline comparisons that change as few factors as possible | Switching models until a good result appears |

Published practice does not mean every historical design should be kept. Operations that learn from data — standardization, imputation, feature selection, threshold selection — must still be fitted only within the training set. The outer results have already been seen, so any follow-up experiment must be labelled a methodological follow-up on existing data and must not be presented as a first independent confirmation.

## Four follow-up stages

### Stage 1: check the existing uncertainty ranges (no retraining)

**Question:** an earlier internal review noted that the handling of tied case–control scores in the interval computation may be wrong. Would that change the reported intervals?

**Background:**
- AUC can be read as the probability that, for a randomly chosen patient and control, the model ranks the patient higher; ties count as half correct.
- It measures ranking ability and says nothing directly about the number of missed diagnoses or whether probabilities are accurate.
- An interval describes the uncertainty of the estimate, not per-person correctness.

**PROPOSED:**
- Check the saved predictions for tied case–control scores, by site and model.
- No ties: keep an aggregate-level proof.
- Ties present: recompute the affected intervals with the correct algorithm, keeping the original resampling scheme and random indices, and compare them with the original intervals; do not overwrite the frozen artifacts.

**Deliverables:**
- A table of tie counts;
- Where needed, a before-and-after interval comparison;
- A statement of whether the conclusions change.

This is an audit of existing predictions, not new training. Until the check is done, it cannot be said that the issue has no effect (NOT VERIFIED).

### Stage 2: document the input sources (recover the records first)

**Question:** where do the 98 volume scores and the 424 functional time-series columns each come from?

**PROPOSED:** recover the logs and generating scripts and record, item by item:
- **Structural:** segmentation version, atlas and column order, space, units, and the definition of total intracranial volume (TIV).
- **Functional:** original repetition time and cached sampling, registration, denoising, filtering, frame censoring and effective length.

Mark each item as verified, explicitly not performed, or unknown.

**Also standardize the following wording:**
- A model that includes TIV is not called "imaging-free";
- A fusion comparison does not mean confounding has been removed;
- A planned re-analysis is not called a "confirmed prospective registration";
- Keep the original cross-validation and LOSO criteria.

Targeted inspection of the original images is scheduled only if quality concerns arise or stronger anatomical evidence is needed.

**Deliverables:** one provenance table each for the structural and functional inputs, with evidence for every field or an explicit gap. Information that cannot be recovered must not be filled in by guesswork; this limits any reproducibility claims.

### Stage 3: run only one experiment that explains the instability (fix the design first)

**Question:** does the selection of fusion weights depend too much on one small validation set?

**PROPOSED:**
- Fix the outer test sites, input features and core model comparison.
- Prespecify the number of inner splits and the random seeds, and compare the original strategy with one named alternative.
- State whether the inner score agrees with the within-site discrimination that the outer evaluation targets.
- Report each site's increment, the weight distribution and any sign changes.

**Design constraints:**
- The basic-information model, basic information plus functional, and the model that adds structural features must use the same outer participants.
- Test sites take no part in scaling, feature selection, weight selection or choosing between strategies.
- Changing the inner cross-validation, the scoring target and the refitting all at once measures the effect of the whole pipeline and cannot be attributed to any single change.

**Deliverables and stopping conditions:**
- Report improvement, no change or worsening in full.
- The goal is stability; matching any paper's score is not an acceptance criterion.
- Repeating random seeds does not add independent participants and does not by itself provide a whole-pipeline confidence interval.

### Stage 4: decide from the claim whether external data are needed

**If the aim is to explain method sensitivity within ADHD-200:** a re-analysis evidence package of limited scope can come first. Whether external data are required depends on the claim itself and on reviewers' requirements.

**If the aim is to claim stable cross-cohort prediction:**
- First check candidate data: cases and controls, diagnostic procedure, age, whether both MRI modalities are paired, whether processing pipelines are compatible, and any overlap with the development or pretraining data.
- Distinguish two approaches: transferring a frozen model directly, and retraining on the new cohort with a fixed method. They answer different questions.

**Deliverables and stopping conditions:**
- An applicability assessment table plus a clear validation question; large-scale processing does not start if the conditions are not met.
- The test set from the original ADHD-200 competition must also be checked for prior use in this project; it cannot be treated as new external data just because "holdout" appears in its name.

## Proposed research direction

**PROPOSED:** "Incremental prediction from multisite ADHD imaging fusion: sensitivity to quality control, inner selection and evaluation scheme". This is a research direction, not a written manuscript, and not a confirmed novelty claim.

The results package should answer:
- how much predictive value imaging adds over basic information;
- whether the conclusion holds under a different QC or validation scheme;
- what the existing decomposition analyses and the new pipeline comparisons each explain;
- which questions still need new data or manual image review.

If there is no stable increment, keep the bounded result under its stated conditions; if a stable increment appears, move on to independent validation. A positive average cannot be taken to imply diagnostic use.

## Limitations

**Not yet done:**
- checking the actual effect of the tie issue;
- recovering the input sources;
- any new training;
- external validation.

**Literature:**
- The full text of MATNet could not be obtained. Unreadable full texts and preprints were not treated as checked methodological evidence.
- The papers differ in task, age range, QC, inputs and splitting, so accuracies and AUCs cannot be mixed in one comparison, and reliability cannot be judged by the highest score.
- A limited search cannot show that this project's research idea is original.
