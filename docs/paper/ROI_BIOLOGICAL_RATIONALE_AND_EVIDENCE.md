# Biological rationale for the ROI choices and evidence mapping

**Status labels:** VERIFIED = checked against code, data records or sources; INFERRED = inference supported by evidence; PROPOSED = suggested but not executed; NOT VERIFIED = not yet checked.

## 0. Summary

The regions chosen for the early ROI-guided CNN branch (frontal cortex, cingulate cortex and the thalamo-striatal system) **correspond to an established and repeatedly replicated hypothesis in ADHD neuroimaging**: the fronto-striatal(-thalamic) circuit dysfunction model. The teaching notebook that motivated this choice (`ADHD_sliceCNN.ipynb`, cell 54; not part of this repository) gives a complete, internally consistent argument for it, but **cites no literature**. This document does four things:

1. Verifies which atlas, which regions and which feature columns the code actually used (VERIFIED, from the git history and the atlas code).
2. Matches the notebook's biological argument, point by point, to published evidence retrieved from PubMed (all references in section 3 come from PubMed and include DOIs).
3. Verifies the atlas or tool behind each of the project's three feature routes: the early 20 intensity columns, the later 98 structural volumes and the 424-dimensional functional connectivity. They are Harvard-Oxford, SynthSeg 2.0 (Desikan-Killiany-style cortex plus standard subcortical segmentation) and the official BrainLM A424 atlas (Glasser HCP-MMP cortex plus subcortex and cerebellum; **not** "AAL-424" as previously recorded). The three are distinct and must not be conflated (sections 3a–3d).
4. Uses the hypothesis to restrict the feature set and runs one same-protocol CV comparison for each of the structural and functional representations, **testing with data whether the hypothesis-defined regions predict better than whole-brain automatic segmentation or all connections** (sections 6 and 7).

**Important boundary:** the literature supports the broad hypothesis that the fronto-striato-thalamic circuit is functionally and structurally abnormal in ADHD. It does not show that the specific combination of 15 subregions chosen here reflects the papers the notebook author had in mind. Section 4 states this explicitly.

### Summary of empirical results (2026-09-18, CV only, primary cohort of 350 participants)

When the hypothesis was used to restrict the feature set, **structure and function gave opposite answers**:

| Modality | Biological subset | All features | Result |
|---|---:|---:|---|
| Structural (SynthSeg volumes, 36/98 regions ≈ 37%) | LR 0.5673 / MLP 0.5665 | LR 0.6176 / MLP 0.6239 | **Clearly worse after restriction**; lower in 5 of 5 repeats, by 0.05–0.06 AUC |
| Functional (tangent connectivity, 148/424 nodes ≈ 35%) | LR 0.6207 / MLP 0.6247 | LR 0.6152 / MLP 0.6210 | **Roughly equal, slight advantage**; 3 of 5 repeats, difference below 0.01 AUC |

Both experiments reproduced the corresponding all-feature baseline with identical frozen splits and model settings, and matched the published numbers almost exactly (structural LR 0.617601 vs 0.6176; functional LR 0.615238 vs 0.6152). The comparison is therefore trustworthy rather than an artifact of a faulty data reconstruction.

**This should not be summarized as "the biological hypothesis is wrong for structure and right for function."** The additional structural diagnostics (section 6) suggest that whole-brain automatic segmentation performs better partly because diffuse, strongly age-related structures such as white matter and ventricles enter the model and provide an implicit route to age confounding; restricting to the hypothesis regions cuts that route. Functional connectivity features have a different dimensional structure (node pairs rather than single nodes, with ANOVA edge selection already filtering redundancy), so adding whole-brain data offers limited marginal gain. The actual finding is that **restricting features by a literature hypothesis has asymmetric consequences, with different mechanisms, for structural volumes and functional connectivity**. This belongs in the methods limitations of a paper and is not a simple positive or negative result.

## 1. Atlas and regions actually used by the code (VERIFIED)

Source: `utils/roi.py` (removed from the main branch; readable in the history at `a43460c^:utils/roi.py`).

- **Atlas:** Harvard-Oxford (`cort-maxprob-thr25-2mm` + `sub-maxprob-thr25-2mm`, obtained through nilearn).
- **Cortical regions (10, not lateralized, because the cort-maxprob atlas is not lateralized):**
  Frontal Pole; Superior Frontal Gyrus; Middle Frontal Gyrus; Inferior Frontal Gyrus, pars triangularis; Inferior Frontal Gyrus, pars opercularis; Frontal Medial Cortex; Frontal Orbital Cortex; Paracingulate Gyrus; Cingulate Gyrus, anterior division; Cingulate Gyrus, posterior division.
- **Subcortical regions (5 × left/right = 10):** Thalamus, Caudate, Putamen, Pallidum, Accumbens (the sub-maxprob atlas is lateralized).
- In total 10 + 10 = **20 regions**, matching the comment "20 atlas ROI mean subject-zscored T1 intensities" in `reproduction/legacy/build_multimodal_manifest.py:286` and the assertion in `run_functional_fusion.py:159-161` that `roi_columns` has length 20. This identifies the 20 anatomical regions behind the historical 20-column ROI feature set.
- **These 20 regions had two distinct roles in the early pipeline:**
  1. As a **mask** that determines which axial T1 slices the ROI-guided CNN extracts (slice selection, not a tabular feature).
  2. As **20 tabular features** (within-subject z-scored mean T1 intensity per region) for the later LR fusion model (`run_functional_fusion.py`).
  The code comment states "not volume or cortical thickness": **these 20 columns are mean intensities, not volumes or cortical thickness.**

## 2. Biological argument in the teaching notebook (VERIFIED, `ADHD_sliceCNN.ipynb`, cell 54)

The notebook groups the 20 regions into three functional modules and justifies each:

| Module | Regions | Rationale given in the notebook |
|---|---|---|
| Prefrontal cortex (executive control) | Frontal pole, superior, middle and inferior frontal gyri (pars triangularis/opercularis), medial frontal, orbitofrontal | Sustained attention, behavioral inhibition, working memory and decision-making, matching core ADHD symptoms |
| Cingulate cortex (attention allocation and conflict monitoring) | Paracingulate, anterior and posterior cingulate | Anterior cingulate: conflict monitoring, error detection and attention allocation; posterior/paracingulate: self-monitoring, linked to insufficient default mode network (DMN) suppression during tasks |
| Thalamo-striatal system (classic core circuit) | Thalamus, caudate, putamen, pallidum, accumbens | The prefrontal → striatum → thalamus → prefrontal loop supports behavioral initiation and inhibition, impulse control and reward motivation; the accumbens relates to reward sensitivity, and the circuit is the target of dopaminergic medication |

The notebook cites no specific papers; section 3 supplies them from PubMed.

## 3. Matching published evidence (VERIFIED, retrieved from PubMed; see the reference list)

| Notebook argument | Reference | What the reference concludes | Direct support for the notebook's statement? |
|---|---|---|---|
| The fronto-striatal circuit is the core neurobiological basis of ADHD | Bush, Valera & Seidman 2005 [1] | Review: fronto-striatal structural and functional dysfunction (lateral prefrontal cortex, dorsal anterior cingulate, caudate, putamen) is likely part of ADHD pathophysiology | Direct support; its region list (lateral PFC, dorsal ACC, caudate, putamen) overlaps strongly with this project |
| PFC, ACC, basal ganglia and thalamus are commonly hypoactivated in functional imaging | Dickstein, Bannon, Castellanos & Milham 2006 (ALE meta-analysis) [2] | Voxel-wise meta-analysis of 16 functional imaging studies: consistent hypoactivation in anterior cingulate, dorsolateral prefrontal, inferior prefrontal cortex, basal ganglia and thalamus | Direct support; the regions cover nearly all 15 named regions in this project |
| Striatal abnormalities on structural imaging | Ellison-Wright, Ellison-Wright & Bullmore 2008 (structural meta-analysis) [3] | Meta-analysis of 7 voxel-based morphometry studies: reduced grey matter in the right putamen/pallidum in ADHD, an anatomical marker of the fronto-striatal circuit | Direct support for the pallidum and putamen as structural regions of interest |
| Dorsal fronto-striatal circuits support cognitive control; ventral circuits support reward | Durston, van Belle & de Zeeuw 2010 [4] | Distinguishes dorsal fronto-striatal (cognitive control) and orbitofronto-striatal (reward processing) circuits as a model for neurobiological subtypes of ADHD | Supports the notebook's distinction between caudate/putamen (behavioral control) and accumbens (reward sensitivity) |
| Posterior cingulate/DMN relates to insufficient task-related suppression | Castellanos & Proal 2012 [5] | Extends the classic fronto-striatal model to large-scale resting-state networks such as the DMN and relates the DMN to behavioral variability in ADHD | Supports the notebook's DMN statement for the posterior/paracingulate cortex, but as a network-level hypothesis rather than region-by-region causal evidence |
| Recent integrated structural and functional evidence | Mizuno et al. 2025 (review) [6] | T1 imaging shows reduced grey matter in frontal, basal ganglia and cerebellar regions and delayed cortical maturation; rs-fMRI shows altered DMN, fronto-parietal and salience network connectivity | A 2025 synthesis confirming that the hypothesis remains a mainstream framework rather than an outdated theory |

## 4. Limitations that must be stated (NOT VERIFIED; not to be glossed over)

1. **This is not region-by-region causal evidence.** The references support the broad fronto-striato-thalamic hypothesis. Most are **meta-analyses or reviews** reporting **group-level statistical effects**, which do not guarantee that a region discriminates ADHD at the individual level. This repository's own results show the difference: under strict LOSO the ROI-CNN reached a pooled OOF AUC of only 0.470, below the 0.619 of the age + sex baseline. A valid biological hypothesis and reliable individual prediction are different claims, and classification weights, attribution maps and statistical associations are not causal mechanisms.
2. **These are not necessarily the sources the notebook author consulted.** The six references were retrieved because their content closely matches the notebook's argument; the notebook records no citations, so they cannot be presented as its original basis. Any formal citation should rest on whether their scientific content holds, not on a claim of original provenance.
3. **The atlas behind each of the three feature routes (20 historical ROI features, 98 later structural features, 424 functional features) is now verified, and the three are distinct:**

### 3a. 20 historical features = Harvard-Oxford (VERIFIED, section 1)

15 named regions (10 cortical + 5 × 2 subcortical), verified verbatim from `utils/roi.py`.

### 3b. 424 functional features = official BrainLM A424 atlas: Glasser HCP-MMP cortex + subcortex + cerebellum (VERIFIED on 2026-09-18 against the original atlas file; corrects an earlier record)

**Correction:** an earlier version of this document stated "A424 = AAL-424 atlas", based on a secondhand description (the BrainLM Hugging Face model card). The original atlas definition file was then located and parsed in the official BrainLM repository (`github.com/vandijklab/BrainLM`; the same repository that cell 4 of `ADHD_fMRI_BrainLM_A424.ipynb` clones): `toolkit/atlases/A424.dlabel.nii` (CIFTI format with an embedded label table for all 424 regions). **The "AAL-424" label is an inaccurate secondhand description; the atlas is a different one:**

- **Indices 1–360 (cortex, 360 regions):** names such as `R_V1_ROI`, `L_p24_ROI` and `R_8Av_ROI` follow the standard 180-regions-per-hemisphere naming of **Glasser et al. 2016 (HCP Multi-Modal Parcellation, MMP1.0)**, not AAL naming (AAL regions are named like "Frontal_Sup_L").
- **Indices 361–396 (subcortex and thalamus, 36 regions):** `mAmyg/lAmyg` (medial/lateral amygdala), `rHipp/cHipp` (anterior/posterior hippocampus), `vCa/dCa` (ventral/dorsal caudate), `GP` (globus pallidus), `NAC` (nucleus accumbens), `vmPu/dlPu` (ventromedial/dorsolateral putamen), and eight connectivity-defined thalamic zones per hemisphere (`mPFtha` medial prefrontal, `mPMtha` medial premotor, `Stha` somatosensory, `rTtha/cTtha` temporal, `PPtha` posterior parietal, `Otha` occipital and `lPFtha` lateral prefrontal thalamus). The naming follows the classic approach of defining thalamic zones by their cortical connectivity targets (for example, Behrens et al. probabilistic tractography parcellation); the exact source was not exhaustively verified.
- **Indices 397–424 (cerebellum, 28 regions):** `Left/Right/Vermis_I-IV`, `_V`, `_VI`, `_Crus_I`, `_Crus_II`, `_VIIb`, `_VIIIa`, `_VIIIb`, `_IX`, `_X`, the standard lobular naming for the left and right hemispheres and vermis.
- 360 + 36 + 28 = **424**, exactly matching the dimension used in the project.

**The column-order mapping is verified, not assumed.** The extraction loop of `convert_fMRIvols_to_A424()` in the official tool script `toolkit/BrainLM_Toolkit.py` is:
```python
for i in range(1, nParcels + 1):
    ind = (label == i)
    ...
    pmTS[:, i - 1] = np.nanmean(y, axis=1)
```
Output column `i-1` (0-based) corresponds to atlas integer label `i` (1-based), matching the key numbering of the dlabel label table. **Column j (j = 0..423) of the project's `timeseries.npz` therefore has the anatomical name of key j+1 in the dlabel label table.** Each link of this chain (the cloned official repository → the official extraction code → the official label table) was checked directly.

**Conclusion:** A424 is a composite atlas defined by the BrainLM team (Glasser HCP-MMP cortex + Tian/Melbourne-style subcortex + standard cerebellar lobules). It is a **third, fully independent atlas system** alongside Harvard-Oxford (ROI-CNN) and SynthSeg/Desikan-Killiany (98 structural features); region definitions, naming and granularity differ, and there is no shared anatomical definition linking the three directly.

### 3c. Mapping Glasser's 360 cortical regions to a prefrontal/cingulate subset (VERIFIED on 2026-09-18, complete with zero missing names)

The mapping uses the widely cited, community-maintained lookup table `HCP-MMP1_UniqueRegionList.csv` (`bitbucket.org/dpat/tools`), whose grouping matches the 22 functional modules in the supplementary material of Glasser et al. 2016 (*Nature*, [DOI](https://doi.org/10.1038/nature18933)). Archived copy: [reproduction/exploratory/a424_atlas_reference/HCP-MMP1_UniqueRegionList.csv](../../reproduction/exploratory/a424_atlas_reference/HCP-MMP1_UniqueRegionList.csv).

**Selected cortical modules** (matching the prefrontal and cingulate regions of the original Harvard-Oxford hypothesis; insula, motor, somatosensory and other modules outside the original hypothesis are excluded):

| Glasser module | Regions per hemisphere | Original hypothesis region |
|---|---:|---|
| Anterior_Cingulate_and_Medial_Prefrontal | 16 | Anterior cingulate + medial frontal cortex |
| Dorsolateral_Prefrontal | 13 | Superior/middle frontal gyrus |
| Inferior_Frontal | 9 | Inferior frontal gyrus, pars triangularis/opercularis |
| Orbital_and_Polar_Frontal | 9 | Frontal pole + orbitofrontal cortex |
| Posterior_Cingulate | 13 | Posterior cingulate |

60 regions per hemisphere × 2 = **120 cortical nodes**.

**Mapping method and check:** A424 node names follow `{L|R}_{region code}_ROI` (for example `L_a24_ROI`), which can be built from the lookup table's `LR` and `region` columns. Every row of the five selected modules was converted to `{LR}_{region}_ROI` and looked up among the 424 actual labels: **all 120 were found, with none missing.**

**Together with the 28 verified subcortical and thalamic nodes** (ventral/dorsal caudate, ventromedial/dorsolateral putamen, globus pallidus, accumbens and the eight functional thalamic zones, each per hemisphere; amygdala and hippocampus excluded, matching the structural exclusion criteria), **the functional biological subset contains 148 nodes, 35% of all 424**. This is close to the structural proportion of 36/98 ≈ 37%, so the degree of restriction is comparable between modalities.

Full node index: [reproduction/exploratory/a424_atlas_reference/a424_biological_subset_node_indices.txt](../../reproduction/exploratory/a424_atlas_reference/a424_biological_subset_node_indices.txt). The functional comparison that uses this subset is reported in section 7.

### 3d. 98 later structural features = SynthSeg 2.0 (VERIFIED on 2026-09-17 against the original run records)

The repository contains no segmentation step: `run_structural_fusion_v2.py` and `run_structural_fusion_locked.py` consume a precomputed `volume_fractions` array, neither manifest lists a segmentation script, and the project notebooks contain no aparc/aseg/FreeSurfer/FastSurfer/SynthSeg/Desikan step. The generation chain was verified read-only from the original SynthSeg run records in the private analysis workspace, without modifying or rerunning anything:

- **Tool:** SynthSeg 2.0 with the model weights distributed by FreeSurfer. `model_provenance.json` records `synthseg_2.0.h5`, `synthseg_parc_2.0.h5` and `synthseg_qc_2.0.h5`, each downloaded from the official `surfer.nmr.mgh.harvard.edu` server and SHA256-checked, pointing to the official FreeSurfer repository `github.com/freesurfer/freesurfer`.
- **Mode:** `protocol.json` records "SynthSeg2.0 standard with parcellation, volumes, QC, resampled image": the standard (not fast/robust/crop) mode with cortical parcellation (`--parc`), volume output and automatic QC.
- **Scale:** a three-participant feasibility pilot on 2026-09-07 (one each from NYU, OHSU and NeuroIMAGE, each producing "101 volume measurements and 8 predicted QC scores") was followed by batch runs on 2026-09-08 and 2026-09-09 (17 batches × 21 participants = 357), directly preceding the `structural_qc_locked_20260909` locked QC cohort.
- **101 → 98, verified column by column:** comparing the 101 pilot output headers with the 98 columns actually used in `volumes_NOT_TRAINING_READY.npz` gives exactly three removed columns: `total intracranial` (TIV, kept separately as `total_intracranial_mm3` rather than as a regional volume) and `left cerebral cortex` / `right cerebral cortex` (coarse whole-hemisphere cortex totals that duplicate the 68 Desikan-Killiany cortical regions and were removed to avoid redundancy and collinearity). **No other region was added, removed or renamed**; the remaining 98 names match exactly.
- **Citable method:** for cortical parcellation, automatic QC and intracranial volume, the official SynthSeg README asks users to cite Billot, Magdamo, Cheng, Arnold, Das & Iglesias, "Robust machine learning segmentation for large-scale analysis of heterogeneous clinical brain MRI datasets," *PNAS* 2023;120(9):e2216399120. [DOI](https://doi.org/10.1073/pnas.2216399120) (verified in PubMed, PMID 36802420).

**Conclusion:** the early ROI-CNN used the Harvard-Oxford atlas to select 15 hypothesis-driven regions, whereas the later 98 structural features come from **whole-brain automatic segmentation** with SynthSeg 2.0 rather than a hypothesis-driven subset. **The two routes are anatomically independent; the later features do not inherit the fronto-striato-thalamic scope of the earlier ones.** The biological hypothesis (sections 2 and 3) shaped the original ROI-CNN design but not the feature engineering of the later structural + functional fusion analysis, which uses assumption-free whole-brain segmentation and learned model weights. A paper's methods section must describe these two designs separately rather than referring generally to "ADHD-related brain regions".

## 5. Remaining work (PROPOSED, not executed)

1. If a manuscript needs the exact names of the 98 regions, they can be read from the column headers of one SynthSeg output CSV and checked against SynthSeg's built-in cortical atlas naming. This was not needed to establish the tool's identity.
2. The methods should state explicitly that the early ROI-CNN used hypothesis-driven region selection (Harvard-Oxford, 15 regions) while the later structural + functional fusion analysis used whole-brain automatic segmentation (SynthSeg 2.0, no prior selection). These are different design philosophies, and the later analysis does not inherit the earlier anatomical hypothesis.
3. Before the references in section 3 are cited formally, a human reviewer should check each abstract against the claimed support. The DOIs were verified to exist, but the references were not read in full for citation fit.

## 6. Exploratory comparison: biological subset vs whole-brain automatic segmentation (2026-09-18, CV only)

This section tests directly whether restricting the 98 automatically segmented regions to the fronto-striato-thalamic core circuit supported by biological evidence performs as well as, or better than, the full segmentation.

### Design

- **Feature subset:** from the 98 SynthSeg columns verified in section 3d, **36 columns** were selected by exact Desikan-Killiany cortical and subcortical structure names: 9 prefrontal subregions (including the frontal pole), 4 cingulate subregions (caudal/rostral anterior cingulate, posterior cingulate, isthmus) and the thalamus, caudate, putamen, pallidum and accumbens, each for both hemispheres. **Amygdala and hippocampus are excluded**: the original teaching notebook marks them as optional "extended/limbic" regions and does not use them (`USE_EXTENDED=False`), and this experiment keeps that boundary. Full column list: [`results/structural_biological_subset_cv_20260918/bio_subset_columns.json`](../../results/structural_biological_subset_cv_20260918/bio_subset_columns.json).
- **Data and splits:** the frozen `primary` QC cohort (350 participants) and the original 5 × 3-fold split assignments (`runs/demographic_increment_20260908_locked_v2/splits.csv`), with **no new splitting**.
- **Models:** identical to the frozen `run_structural_fusion_locked.py`: L2 logistic regression (C ∈ {0.01, 0.1, 1, 10}, chosen by validation AUC, ties to the smaller C) and a 64/16 GELU MLP (3 seeds, 1200/2200/3200 + fold, equal-weight ensemble), with StandardScaler fitted on training folds only.
- **Scope:** CV only; LOSO was not run in this round. The new script [`reproduction/exploratory/structural_biological_subset_cv.py`](../../reproduction/exploratory/structural_biological_subset_cv.py) reads the original frozen data read-only, **modifies no frozen file** and writes to a new run directory; aggregate outputs are in [`results/structural_biological_subset_cv_20260918/`](../../results/structural_biological_subset_cv_20260918/).
- **Validity check:** the same script refits the full 98-column baseline with identical code (`structural_lr_full98` / `structural_mlp_full98`). This is an internal consistency check of the data, splits and training, not a replacement for the published numbers.

### Results

| Model | Biological subset (36 columns), CV mean | All 98 columns, CV mean (this rerun) | All 98 columns, CV mean (published) | Difference |
|---|---:|---:|---:|---:|
| Logistic regression | 0.5673 | 0.6176 | 0.6176 | **−0.0503** |
| MLP | 0.5665 | 0.6239 | 0.6256 | **−0.0574** (−0.0591 against the published value) |

The rerun of the full 98-column logistic regression **matches the published number exactly** (0.617601 vs 0.6176), and the MLP rerun differs by 0.0017, within neural-network training noise. The rerun is therefore trustworthy and the two sets of numbers are directly comparable.

Per repeat ([`repeat_metrics.csv`](../../results/structural_biological_subset_cv_20260918/repeat_metrics.csv)), **the biological subset was lower than all 98 columns in 5 of 5 repeats for both logistic regression and the MLP**. The gap is a consistent direction rather than a mean pulled down by a few folds.

### Interpretation boundaries

1. **This is a single exploratory CV run, not the project's confirmatory statistical framework.** It has no Nadeau-Bengio corrected intervals, TOST equivalence tests or site-stratified bootstrap, as used in the v2 analysis; "5 of 5" is a descriptive consistency observation, not a significance result. Inclusion in a paper would require formal uncertainty quantification to the project's existing standard.
2. **This does not show that the fronto-striato-thalamic hypothesis is wrong.** It shows only that, with these SynthSeg volume features and these LR/MLP settings, restricting to the 36 regions predicts worse than using all 98. Possible explanations include, but are not limited to: (a) the hypothesis holds at the group level, but 98 features give the model more usable variance (possibly unrelated to ADHD) than 36; (b) the full set lets the model implicitly use confounding information such as TIV and whole-brain volume, which relate to covariates like site and motion rather than to anatomy; (c) coarse volume may not be the measure through which these regions carry signal, since much of the hypothesis rests on functional activation and connectivity rather than grey matter volume. This design cannot distinguish between these explanations.
3. **The result agrees with the direction of the repository's other findings.** Neither the early ROI-guided CNN (Harvard-Oxford; strict-LOSO pooled OOF AUC 0.470, below the 0.619 age + sex baseline) nor this SynthSeg biological subset improved performance by restricting features with a literature hypothesis. This consistent negative pattern is worth stating in a paper, but the mechanisms differ between attempts and should not be merged into one sentence.

### Outputs

- [`reproduction/exploratory/structural_biological_subset_cv.py`](../../reproduction/exploratory/structural_biological_subset_cv.py): new, non-frozen script
- [`results/structural_biological_subset_cv_20260918/`](../../results/structural_biological_subset_cv_20260918/): `summary.csv`, `repeat_metrics.csv`, `fold_metrics.csv`, `bio_subset_columns.json`, `status.json`

## 7. Functional comparison: biological subset (148 nodes) vs all 424 nodes (2026-09-18, CV only)

Given the structural result, the same comparison was run for fMRI, using the 148-node biological subset verified in section 3c and the matching tangent-space functional connectivity pipeline.

### Design

- **Feature subset:** 148 nodes (120 cortical nodes from the Glasser module mapping in section 3c and 28 subcortical and thalamic nodes from section 3b), with the same exclusions as the structural hypothesis (no amygdala or hippocampus).
- **Covariance reuse:** the 148 × 148 submatrices are sliced from the frozen, hash-checked `covariances.npy` (378 × 424 × 424, computed from the original 424-dimensional time series). Ledoit-Wolf covariances were **not recomputed**, because the covariance of a subvector is exactly the corresponding submatrix of the full covariance; this step is exact, not approximate.
- **All other steps match the frozen code:** training-only geometric mean (`_geometric_mean`, max_iter=100, tol=1e-8) → tangent-space log map (`refine_tangent_reference.transform`) → ANOVA top-1000 edge selection (`select_features`, k=1000, the same k as for all 424 nodes, not scaled down with the smaller number of edges) → the same LR (C grid search) and MLP (3-seed ensemble).
- **Scope:** as for the structural comparison, CV only (primary cohort, 350 participants, 5 × 3 folds); LOSO was not run.
- **Validity check:** the same script reproduces the all-424-node baseline. `tangent_lr_full424` has a CV mean of 0.6152, **exactly matching** the published 0.6152; `tangent_mlp_full424` has 0.6210 against the published 0.6205 (a 0.0005 difference, within neural-network training noise). The rerun is trustworthy.

Engineering note: without a thread limit, one fold took about 9,000–10,000 seconds, which would have taken close to 40 hours for 15 folds. With `threadpool_limits(limits=4)` (the same setting as the frozen code), one fold took about 950–1,000 seconds and the whole run **about 4 hours**. Unrestricted BLAS threads oversubscribed the CPU; the computation itself was not the bottleneck. Similar full-node geometric-mean computations should apply the same limit.

### Results: the direction is opposite to the structural result, but the difference is small and inconsistent

| Model | Biological subset (148 nodes) | All 424 nodes (this rerun) | All 424 nodes (published) | Difference |
|---|---:|---:|---:|---:|
| Logistic regression | 0.6207 | 0.6152 | 0.6152 | **+0.0055** |
| MLP | 0.6247 | 0.6210 | 0.6205 | **+0.0037** |

Per repeat ([`repeat_metrics.csv`](../../results/a424_biological_subset_cv_20260918/repeat_metrics.csv)), the biological subset won **3 of 5 repeats** for logistic regression and **3 of 5** for the MLP. Unlike the consistent 5 of 5 structural result, this is a weak majority with a difference below 0.01 AUC. With only five repeats and no formal interval estimate, it is closer to "roughly equal, possibly a slight advantage" than to a defensible positive result.

### Structure vs function

| | Structural (volume) | Functional (tangent connectivity) |
|---|---|---|
| Proportion retained | 36/98 ≈ 37% | 148/424 ≈ 35% |
| Biological subset vs all | **Clearly worse** (−0.05 to −0.06; lower in 5 of 5 repeats) | **Roughly equal, slight advantage** (+0.004 to +0.006; 3 of 5) |

The opposite directions show that restricting features by a literature hypothesis has different consequences for the two representations. Section 6 offers one explanation for the structural side: whole-brain volumes include diffuse, strongly age-related signal that the restriction removes. On the functional side, discriminative information is distributed differently: connections are node pairs rather than single nodes, the 424-node set includes many connections unrelated to the hypothesis regions, and ANOVA selection already filters redundant edges, so the marginal gain from whole-brain data is small or absent. **This should not be generalized to "the biological hypothesis holds for function but not for structure."** More precisely, the two feature representations differ in how sensitive they are to restricting the prior region set, which is itself a finding for the methods limitations of a paper.

### Outputs

- [`reproduction/exploratory/a424_biological_subset_cv.py`](../../reproduction/exploratory/a424_biological_subset_cv.py): new, non-frozen script
- [`results/a424_biological_subset_cv_20260918/`](../../results/a424_biological_subset_cv_20260918/): `summary.csv`, `repeat_metrics.csv`, `fold_metrics.csv`, `status.json`

## References

Retrieved from PubMed:

1. Bush G, Valera EM, Seidman LJ. Functional neuroimaging of attention-deficit/hyperactivity disorder: a review and suggested future directions. *Biol Psychiatry*. 2005;57(11):1273-84. [DOI](https://doi.org/10.1016/j.biopsych.2005.01.034)
2. Dickstein SG, Bannon K, Castellanos FX, Milham MP. The neural correlates of attention deficit hyperactivity disorder: an ALE meta-analysis. *J Child Psychol Psychiatry*. 2006;47(10):1051-62. [DOI](https://doi.org/10.1111/j.1469-7610.2006.01671.x)
3. Ellison-Wright I, Ellison-Wright Z, Bullmore E. Structural brain change in Attention Deficit Hyperactivity Disorder identified by meta-analysis. *BMC Psychiatry*. 2008;8:51. [DOI](https://doi.org/10.1186/1471-244X-8-51)
4. Durston S, van Belle J, de Zeeuw P. Differentiating frontostriatal and fronto-cerebellar circuits in attention-deficit/hyperactivity disorder. *Biol Psychiatry*. 2010;69(12):1178-84. [DOI](https://doi.org/10.1016/j.biopsych.2010.07.037)
5. Castellanos FX, Proal E. Large-scale brain systems in ADHD: beyond the prefrontal-striatal model. *Trends Cogn Sci*. 2012;16(1):17-26. [DOI](https://doi.org/10.1016/j.tics.2011.11.007)
6. Mizuno Y, Yamashita M, Shou Q, Hamatani S, Cai W. A brief review of MRI studies in patients with attention-deficit/hyperactivity disorder and future perspectives. *Brain Dev*. 2025;47(2):104340. [DOI](https://doi.org/10.1016/j.braindev.2025.104340)
