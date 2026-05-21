# Source Code Folder

The current repository stores Colab-exported scripts in `notebooks/`.

For a more maintainable package, future refactoring could move reusable functions here:

```text
src/
├── data_io.py          # BIDS scanning, label loading, manifest creation
├── preprocessing.py    # slice extraction, normalization, registration helpers
├── models.py           # CNN and GNN model definitions
├── evaluation.py       # AUC, bootstrap CI, aggregation, threshold metrics
├── graphs.py           # fMRI ROI time series and graph construction
└── configs.py          # path and experiment configuration
```
