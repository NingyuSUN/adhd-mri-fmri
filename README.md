# ADHD-200 fMRI: reproducible ML/DL evaluation

A multi-site neuroimaging case study by **Ningyu Sun**: audited data, training-only feature engineering, logistic regression and PyTorch MLPs, explicit non-imaging controls, and traceable evaluation.

**Current portfolio release: 378-subject fMRI, frozen 2026-09-08; packaging and evidence replay updated 2026-09-10.** This is an internal research benchmark. It is not an ADHD diagnostic service or a demonstrated externally validated predictor.

[One-page case study](PORTFOLIO_CASE_STUDY.md) · [10-slide technical deck](docs/portfolio/ADHD_fMRI_technical_portfolio.pptx) · [3-minute demo](docs/portfolio/DEMO.md) · [Reproduction guide](REPRODUCIBILITY.md) · [Version index](docs/portfolio/RESULT_VERSIONS.md)

## What the results show

| Input and model | Mean AUC |
|---|---:|
| Pearson connectivity + logistic regression | 0.5933 |
| Pearson connectivity + MLP ensemble | 0.6096 |
| Tangent connectivity + logistic regression | 0.6352 |
| Tangent connectivity + MLP ensemble | **0.6453** |
| Age + sex + site + motion control | **0.7077** |
| Control predictions + tangent MLP predictions | 0.7127 |

Tangent improves over Pearson by **0.0357 AUC for the MLP**, with positive differences in all five repeats. Adding imaging predictions to the fuller non-imaging control yields only **0.0050 mean AUC**, with one negative repeat. These answer different questions: representation quality and incremental predictive information.

Scores average three fold AUCs within each of five repeats. The same 378 people recur across repeats. Ranges and repeat SD are descriptive, not confidence intervals. The 0.7127 model contains non-imaging information. Current results do not establish causal independence, clinical utility, or generalization to new hospitals.

## Engineering evidence

- **Data and splits:** audited 378 people, 211 controls / 167 ADHD; five repeated three-fold subject partitions; 201 training / 51 validation / 126 test people per fold.
- **Features:** A424 parcel time series; Pearson versus tangent connectivity; training-only ANOVA top 1,000 edges and scaling; training-only tangent reference.
- **Models:** LR validation-selects C from 0.01/0.1/1. MLP uses 64/16 hidden units, GELU, dropout, AdamW, early stopping and a fixed three-seed equal ensemble.
- **Correctness:** tested role and label alignment, preprocessing boundaries, tangent fit isolation and validation-only fusion selection. A separate replay checks **35,910 saved test rows**, **60 selected fusion weights** and aggregate metrics against frozen files.
- **Provenance:** [preserved original sources and hashes](src/adhd_portfolio/frozen_v1/sources.json), [aggregate verification](results/fmri_378/verification.json), [fold/repeat outputs](results/fmri_378), and explicit limits on what has been rerun.

## Run a small example

Python 3.12+ is required. In a new environment:

```bash
python -m pip install -e ".[models]"
python -m unittest discover -s tests -v
python -m adhd_portfolio demo --out artifacts/synthetic-demo
```

The demo trains the preserved LR/MLP workflow on **120 synthetic examples**, verifies checkpoint replay and saves learning curves/timing. Its scores are not ADHD results. Each output directory must be new.

To audit the historical results you need the separate local frozen release; to rerun full training you need the documented authorized-data caches and recorded numerical environment. Public aggregates alone cannot reconstruct individual predictions. See [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Project layout

```text
src/adhd_portfolio/       evidence replay, synthetic demo, portable runtime entry
  frozen_v1/             byte-preserved original scientific modules
configs/                 explicit benchmark specification
tests/                   leakage, alignment and numerical-boundary checks
results/fmri_378/         verified aggregates; no individual records
figures/fmri_378/         charts generated from those aggregates
docs/portfolio/          short case, technical deck, demo and version notes
notebooks/               historical Colab experiments
```

The earlier 409-person fMRI/BrainLM and structural MRI work remains available as historical extensions. [Structural + functional fusion](docs/structural_functional_fusion.md) is a separate analysis with 350/302/375-person cohorts; its metrics must not be mixed with this table. The running structural v2 was not included in this release.

## Ownership and reuse

Ningyu Sun led the research design, implementation and interpretation with AI-assisted development/review. Claims here describe mentor-led work; no student-only authorship claim is made. Code: MIT. ADHD-200 data retain their source terms and are not redistributed. [Model card](MODEL_CARD.md) · [Data guide](DATA.md).
