# Limitations

## Dataset and labels

ADHD-200 combines sites with different scanners, protocols, recruitment, class prevalence, age distributions, and sex distributions. ADHD itself is heterogeneous, and binary diagnosis labels do not capture subtype, symptom severity, comorbidity, medication, or developmental trajectories.

## Confounding

Age, sex, motion, and QC variables are strongly predictive. This does not mean they are valid biomarkers. They can encode recruitment and acquisition differences or diagnosis-correlated behavior. Any model using these variables must be interpreted as a confound baseline, not a diagnostic solution.

## Site generalization

Strict LOSO is intentionally difficult and better reflects transport to an unseen acquisition site. Some sites are small or single-class, so not every site contributes an estimable held-out AUC. Macro AUC is consequently uncertain and should be read together with site-wise results and bootstrap intervals.

## Structural MRI

The structural branch relies heavily on 2D slices and predefined ROIs, with one pretrained Swin-T experiment. These are practical baselines but do not exhaust volumetric or self-supervised methods. The matched confound baselines and strict site-held-out results nevertheless prevent interpreting the tested structural models as robust biomarkers.

## fMRI preprocessing

The work uses public derivatives and A424 time series, with additional motion restriction and frame scrubbing in robustness analyses. Nuisance modeling, temporal filtering, atlas choice, scrubbing thresholds, and scan duration can all affect connectivity estimates. The stage-3 cohort is smaller (`n=246`), reducing precision.

## Representation and model capacity

Frozen BrainLM, connectivity summaries, spectral features, selected edges, graph prototypes, and spatial modules do not cover every possible representation. However, repeated failure across strict and within-site checks means a more complex architecture alone is not strong evidence that the current data can support robust prediction.

## Metrics

AUC measures ranking, not calibration or clinical utility. Pooled AUC can be inflated or suppressed by site prevalence, so macro site AUC is primary. Confidence intervals remain wide for several comparisons.

## External validation

The project has no prospective, independently collected external test cohort. The analyses therefore support only a research conclusion within the documented ADHD-200 setting.

## Clinical restriction

No output is validated for diagnosis, screening, treatment selection, or individual risk communication.
