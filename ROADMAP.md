# Roadmap

## Short-term

- Convert Colab-exported `.py` scripts to clean `.ipynb` notebooks.
- Add a single configuration file for all path settings.
- Export current results into clean CSV tables under `results/`.
- Add schematic figures for structural MRI and fMRI pipelines.
- Add a model card describing intended and non-intended use.

## Medium-term

- Run leave-one-site-out validation for structural MRI CNNs.
- Run fMRI connectivity baselines using logistic regression, random forest, and XGBoost on vectorized connectivity matrices.
- Compare GCN against non-GNN baselines.
- Add motion/QC-aware fMRI filtering.
- Add site-stratified performance tables.

## Long-term

- Multimodal fusion of T1 MRI and fMRI connectivity.
- Harmonization experiments such as ComBat or domain-adversarial modeling.
- Interpretability analysis of connectivity edges and ROI contributions.
- Manuscript-style write-up with transparent negative-result reporting.
