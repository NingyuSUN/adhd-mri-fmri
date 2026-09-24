# Project Status

**Status: completed deep-learning case study (September 2026).**

The original goal was to test whether structural MRI and resting-state fMRI could support an ADHD prediction model. That question has been evaluated with subject-level and site-held-out protocols. The project is complete as a research result, although the final result is not a clinically useful predictor.

## Completion checklist

| Component | Status | Outcome |
|---|---:|---|
| Structural MRI baselines | Complete | CNN, multi-slice, ROI-guided, ablation, and strict LOSO analyses performed |
| Structural leakage controls | Complete | Subject-level splitting and aggregation enforced |
| fMRI cohort and A424 extraction | Complete | 445 usable A424 subjects; 409 in evaluable two-class held-out sites |
| Classical fMRI baselines | Complete | FC summaries, selected edges, and spectral features tested |
| Pretrained representation | Complete | Frozen BrainLM embeddings tested; fine-tuning stopped by prespecified gate |
| Confound baselines | Complete | Age, sex, motion/QC, and combined baselines tested |
| Strict nested LOSO | Complete | Training-only preprocessing and model selection |
| Motion robustness | Complete | Restricted cohort, frame scrubbing, and QC analysis |
| Residualization robustness | Complete | Residualization fit within each training fold |
| Within-site validation | Complete | Tested to separate site shift from within-site signal |
| Spatial network modules | Complete | Original and scrubbed module features tested |
| Uncertainty analysis | Complete | Paired subject bootstrap for stage-3 contrasts |
| Final documentation | Complete | Results, limitations, reproducibility, and model card consolidated |
| Structural + functional late-fusion | Complete | QC-locked paired retraining on one frozen protocol, 3 cohorts, 45 folds, replay-verified; `docs/structural_functional_fusion.md` |
| Feature-level reproduction | Complete | 66/66 units accepted (45 CV, 21 LOSO); all 17 model outputs per unit and final fusion weights matched |
| Statistical interpretation and sensitivity decomposition | Complete | CV/LOSO interval interpretation, QC decomposition, selector stability, calibration, and site contribution analyses recorded |
| Tables and figures package | Complete | 14 aggregate CSV tables, 9 publication figures, source manifests, and generation scripts under `results/tables_figures_20260914/` |

## Decision

No tested image-derived model demonstrated stable, confound-independent generalization across sites. The project therefore stops before costly Transformer fine-tuning. The frozen representation failed the prespecified transfer gate, and simpler image features also failed multiple robustness checks.

This is a valid scientific endpoint: it documents a complete multimodal deep-learning workflow, prevents overclaiming, and provides a reproducible benchmark for future work.

## Evidence snapshot

The current evidence package supports exact replay of the frozen feature-level workflow and transparent sensitivity analysis. It does not establish raw MRI preprocessing reproducibility, expert anatomical QC, causal interpretation, external validation, or clinical utility. The three QC cohorts overlap; the LOSO result reflects the executed inner 85/15 training-site split and was not followed by refitting on all six training sites. The model is a research benchmark and must not be used for individual ADHD diagnosis.

## Optional future research

Future work is not required to consider this project complete. If the question is reopened, the most valuable changes would be a larger harmonized dataset, prospective external validation, improved phenotyping, and acquisition-balanced sampling—not merely a more complex neural network.
