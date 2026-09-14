import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from tools.portfolio_quickstart import build_summary, render_markdown, write_report
from tools.validate_public_artifacts import validate_manifest, validate_tables


def test_quickstart_reads_committed_aggregate_contract():
    summary = build_summary()
    assert summary["schema_version"] == "portfolio-quickstart.v1"
    assert len(summary["models"]) == 7
    assert summary["primary_contrast"]["cv_delta_auc"] == pytest.approx(-0.0114)


def test_quickstart_output_is_deterministic(tmp_path):
    summary = build_summary()
    first = tmp_path / "first"
    second = tmp_path / "second"
    write_report(first, summary)
    write_report(second, summary)
    assert (first / "summary.json").read_bytes() == (second / "summary.json").read_bytes()
    assert (first / "summary.md").read_bytes() == (second / "summary.md").read_bytes()


def test_public_manifest_and_table_counts():
    assert validate_manifest() >= 60
    assert validate_tables() == 14


def test_table_headers_have_no_individual_prediction_columns():
    for path in (ROOT / "results/tables_figures_20260914/tables").glob("*.csv"):
        with path.open(newline="", encoding="utf-8") as handle:
            header = set(next(csv.reader(handle)))
        assert not {"subject_id", "participant_id", "prediction", "score"} & header
