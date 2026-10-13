# Project evidence: ADHD MRI/fMRI

## Research ownership and question

I independently carried out this project: data preparation, graph and imaging
model implementation, experiment design and execution, result interpretation,
and reproducibility documentation.

The research question is whether structural MRI or resting-state fMRI adds
predictive information beyond age, sex, site, head motion and quality-control
variables, and whether that information transfers to an unseen acquisition site.

## Evidence at a glance

| Work | Inspectable evidence | What it establishes |
|---|---|---|
| Colab graph modeling | [Archived GCN/GAT source](https://github.com/NingyuSUN/adhd-mri-fmri/blob/755266f388f73955c58a86e8a81b13197052a303/notebooks/05_fmri_connectivity_gnn_colab.py) | Implemented graph models and model iterations; historical exploratory code |
| Controlled imaging benchmark | [Methods](../METHODS.md), [CV results](https://github.com/NingyuSUN/adhd-mri-fmri/blob/84629eaac0e3e621e3002d6259f769e03e8515ec/results/fmri_benchmark_stratified_cv_summary.csv), [site-held-out results](https://github.com/NingyuSUN/adhd-mri-fmri/blob/84629eaac0e3e621e3002d6259f769e03e8515ec/results/fmri_strict_loso_summary.csv) | Matched imaging/confound comparisons under documented subject-level splits |
| Later multimodal analysis | [Protocol](analysis_v2_protocol.md), [contrast table](https://github.com/NingyuSUN/adhd-mri-fmri/blob/84629eaac0e3e621e3002d6259f769e03e8515ec/results/v2_cv_contrast_stats.csv), [statistical interpretation](paper/STATISTICAL_INTERPRETATION.md) | Prespecified comparisons, uncertainty estimates and disclosed post hoc sensitivity analyses |
| Reproducibility and delivery | [Replay acceptance](paper/FRESH_REPRODUCTION_STATUS.md), [machine-readable proof](https://github.com/NingyuSUN/adhd-mri-fmri/blob/84629eaac0e3e621e3002d6259f769e03e8515ec/results/paper_readiness_20260911/fresh_refit/verified_reproduction.json), [CI workflow](../.github/workflows/ci.yml) | Recorded feature-level refitting and automated public-artifact checks |

Pinned result links refer to the audited source commit
`84629eaac0e3e621e3002d6259f769e03e8515ec`. The graph source has its own
historical commit because it is no longer a maintained training entry point.

## Graph implementation and evaluation boundary

The Colab work includes graph convolutional networks (GCNs) and graph attention
networks (GATs). The full-data GAT implementation uses 48 Harvard–Oxford regions,
correlation-matrix rows as node features, and edges where absolute correlation
exceeds 0.3. Two attention layers, global mean pooling and a linear classifier
produce a participant-level prediction.

These experiments were run in Colab. The archived code preserves the modeling
work, but its historical scores are not presented here as independently
reproduced final-test performance. It uses a diagnosis-stratified 80/20 split
and inspects test performance during training. An untouched final evaluation
has not been established for this prototype.

The later controlled benchmarks below use different cohorts, representations
and splits. Their scores and replay evidence must not be attributed to the GNN.

## What the later results mean

The 409-participant fMRI benchmark uses five repeats of four folds, stratified
jointly by site and diagnosis. Preprocessing and model selection are fit using
training data. The published mean AUC is 0.677 for demographic/motion/QC controls
and 0.595 for functional connectivity plus frozen BrainLM features. AUC measures
ranking discrimination; the reported fold standard deviations are not confidence
intervals. BrainLM supplies frozen pretrained representations rather than a
foundation model trained by this project.

Separate nested leave-one-site-out testing evaluates transfer to an unseen site.
The tested imaging methods did not establish a stable improvement over the
confound baseline. The later multimodal v2 analysis also has a conditional
positive primary site-held-out contrast and negative contrasts in the other QC
cohorts. Its equivalence hypothesis was not established. These results support
careful sensitivity analysis, not a claim that imaging can never be informative.

The three v2 QC cohorts overlap and are not independent replication studies.
See the [model card](../MODEL_CARD.md) and
[limitations](../LIMITATIONS.md) for the scope of the conclusions.

## Reproduce a useful public check

From the repository root with Python 3.10 or later:

```bash
python tools/quickstart.py --check
python tools/validate_public_artifacts.py
```

These commands check committed aggregate tables and the public artifact
manifest. They require no participant data and do not train a model. To generate
a readable report, use the [README quickstart](../README.md#five-minute-review).

The historical feature-level replay covers 66 units: 45 cross-validation and
21 site-held-out evaluations, with 17 model outputs per unit. The public proof
records matching predictions, fusion weights and statistical summaries.
This was fresh fitting with the frozen training implementation and derived
time-series/volume inputs; it was not an independently authored algorithm or
a replay of the GNN prototype.

The [full reproduction guide](../reproduction/README.md) specifies the authorized
private derivatives, frozen references, environment locks and isolated output
directories required for refitting. Raw MRI preprocessing reproducibility,
independent external-cohort validation and clinical utility are not established.
