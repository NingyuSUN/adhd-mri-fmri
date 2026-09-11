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

## Leave-one-site-out uncertainty and QC sensitivity

The planned v2 reanalysis did not establish its primary equivalence hypothesis. Its primary LOSO increment was positive (+0.028), while two other QC cohorts gave negative estimates. The original site-stratified bootstrap conditions on fixed sites and models; it omits uncertainty from training and unseen-site sampling. The sign changes do not prove LOSO is invalid or establish the cause of instability.

A [post hoc audit](docs/paper/STATISTICAL_INTERPRETATION.md) corrects NYU's primary pair weight to 67.07% (39.7% is its participant fraction). On common subjects with fixed weights, most of the QC-related shift persists. Further descriptive decomposition implicates the selected final fusion weight. This does not isolate all sources of training/tuning variability or establish causation.

The original corrected CV interval and its df=2 sensitivity do not establish equivalence to ±0.02. Cohorts and repeated folds reuse participants, and the many secondary comparisons are exploratory without family-wise error control.

## External validation

The project has no prospective, independently collected external test cohort. The analyses therefore support only a research conclusion within the documented ADHD-200 setting.

## Clinical restriction

No output is validated for diagnosis, screening, treatment selection, or individual risk communication.
