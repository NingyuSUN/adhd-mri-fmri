# Aggregate-only demo

This demo is the aggregate-only entry point for the repository. It runs without ADHD-200 data, private Google Drive paths, raw MRI, or subject-level predictions:

```bash
python tools/quickstart.py --output-dir artifacts/quickstart
cat artifacts/quickstart/summary.md
```

The command reads the committed primary model and contrast tables, validates their schema, and writes a deterministic JSON/Markdown report. It demonstrates the repository's data contract and reporting path; it does not retrain a model.

The expected schema is recorded in `expected_output.json`. Full feature-level reproduction remains a separate workflow documented in `reproduction/README.md` and requires authorized private inputs.
