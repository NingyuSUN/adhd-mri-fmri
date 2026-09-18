# A424 atlas reference (verified 2026-09-18)

`a424_labels_1to424.txt` — the 424 real region names for BrainLM's A424 atlas,
extracted from the official label table embedded in
`toolkit/atlases/A424.dlabel.nii` in https://github.com/vandijklab/BrainLM
(the exact repository this project's `ADHD_fMRI_BrainLM_A424.ipynb` clones).
Format: `<label_key 1-424> <name>` (key 0 = background, omitted here).

Column-to-label mapping, verified against BrainLM's own
`toolkit/BrainLM_Toolkit.py` (`convert_fMRIvols_to_A424`): time-series column
`j` (0-indexed, 0..423) corresponds to label key `j+1` in this file.

Composition: 1-360 = Glasser et al. 2016 HCP-MMP1.0 cortical parcellation
(180 areas/hemisphere); 361-396 = subcortical + thalamic subdivisions
(amygdala, hippocampus, caudate/putamen/pallidum/accumbens, 8 functionally
defined thalamic zones per hemisphere); 397-424 = cerebellar lobules
(left/right/vermis).

Not "AAL-424" — that label (found via a secondary web search and a BrainLM
Hugging Face model-card sentence) does not match the actual names in this
file; see docs/paper/ROI_BIOLOGICAL_RATIONALE_AND_EVIDENCE.md section 3b for
the correction.

`A424_Coordinates.dat` — MNI coordinates per region, same source repository,
copied for reference (not yet used in this project's analysis).
