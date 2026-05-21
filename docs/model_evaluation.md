# Model Evaluation

## Primary Metric

Subject-level AUC is the primary metric.

AUC measures ranking ability, not accuracy. For example, AUC = 0.70 means that a randomly selected ADHD subject has a higher model score than a randomly selected control subject 70% of the time.

## Why Accuracy Is Not Enough

In imbalanced medical datasets, a model can achieve acceptable accuracy by predicting the majority class. This can produce zero recall for the minority/clinical class.

## Recommended Metrics

- subject-level AUC
- bootstrap 95% CI
- fold-wise AUC
- recall at threshold 0.5
- precision at threshold 0.5
- confusion matrix
- R90-style threshold analysis
- site-wise performance
- leave-one-site-out AUC

## Aggregation

For slice-based models, aggregate slice probabilities to subject probability:

```python
subject_probability = mean(slice_probabilities_for_subject)
```

Alternative aggregation methods, such as max aggregation, should be treated as ablation settings.
