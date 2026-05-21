# Ablation and Site Bias

## Why Ablation Matters

Ablation asks whether each component of the pipeline is actually responsible for model performance.

A model may show a good AUC while relying on unwanted shortcuts such as:

- scanner intensity style
- site identity
- age/sex imbalance
- duplicated subject information
- preprocessing artifacts

## Ablation Factors

| Component | Full model | Ablation |
|---|---|---|
| ROI selection | ADHD-related ROI slices | whole-brain/random slices |
| Registration | MNI152 rigid registration | raw subject space |
| Normalization | z-score normalization | no normalization |
| Aggregation | mean probability | max probability |

## Site-bias Controls

Recommended confound baselines:

1. site-only logistic regression
2. age+sex logistic regression
3. site+age+sex logistic regression

If these baselines approach or exceed the image model, the image model cannot be interpreted as strong evidence for ADHD-specific brain signal.

## Interpretation Rules

- Higher AUC without normalization may indicate scanner shortcut.
- Similar AUC from random slices and ROI slices weakens the ROI hypothesis.
- Strong site-only AUC indicates site-label imbalance.
- Fold inconsistency suggests unstable signal.
