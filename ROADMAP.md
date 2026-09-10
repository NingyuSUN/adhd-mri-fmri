# Roadmap

## Completed project scope

- structural MRI baselines and ablations
- subject-level leakage controls
- strict structural LOSO work
- fMRI connectivity and graph prototypes
- locked fMRI strict nested LOSO benchmark
- frozen BrainLM transfer evaluation
- confound baselines and incremental-value tests
- motion restriction and frame scrubbing
- training-fold residualization
- within-site validation
- spatial network module features
- paired bootstrap uncertainty
- final documentation and model card

## Completion decision

The project is closed as a research benchmark. Transformer fine-tuning is not required because the frozen representation did not pass the prespecified transfer gate and multiple simpler representations failed robustness checks.

## Optional future work

Only reopen the modeling phase if new evidence changes the data problem, for example:

1. a larger and acquisition-balanced training cohort;
2. an independent prospective external test set;
3. richer phenotypes, comorbidity, medication, and symptom targets;
4. stronger harmonization with all parameters fit inside training folds;
5. preregistered success criteria requiring improvement over confound baselines.

Additional architecture sweeps on the same cohort are low priority.
