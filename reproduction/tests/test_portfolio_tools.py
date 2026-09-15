import csv
import json
import py_compile
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from tools.portfolio_quickstart import build_summary, render_markdown, write_report
from tools import validate_public_artifacts as validator
from tools.validate_public_artifacts import validate_manifest, validate_no_notebooks, validate_tables


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


def test_final_package_contains_no_notebooks():
    assert validate_no_notebooks() == 0


def test_private_path_scan_ignores_compiled_validator(tmp_path, monkeypatch):
    cache = tmp_path / "tools" / "__pycache__"
    cache.mkdir(parents=True)
    bytecode = cache / "validate_public_artifacts.pyc"
    py_compile.compile(validator.__file__, cfile=str(bytecode), doraise=True)
    assert any(token.encode() in bytecode.read_bytes() for token in validator.FORBIDDEN)
    monkeypatch.setattr(validator, "ROOT", tmp_path)
    monkeypatch.setattr(validator, "PACKAGE", tmp_path / "package")
    assert validator.validate_no_private_paths() == 0


@pytest.mark.parametrize("token", validator.FORBIDDEN)
@pytest.mark.parametrize("relative_path", [
    "README.md", "docs/example.md", "reporting/example.py",
    "tools/example.py", "tools/__pycache__/leak.txt",
    "demo/example.json", "package/tables/example.csv",
    "reproduction/example.py", "reproduction/legacy/example.py",
])
def test_private_paths_in_public_text_still_fail(tmp_path, monkeypatch, token, relative_path):
    path = tmp_path / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(token + "private-input", encoding="utf-8")
    monkeypatch.setattr(validator, "ROOT", tmp_path)
    monkeypatch.setattr(validator, "PACKAGE", tmp_path / "package")
    with pytest.raises(AssertionError, match="private absolute path in public file"):
        validator.validate_no_private_paths()


def test_complete_public_artifact_validation_after_import(capsys):
    assert validator.main() == 0
    assert json.loads(capsys.readouterr().out)["status"] == "pass"


@pytest.mark.parametrize("separator", ["/", "\\"])
def test_windows_drive_paths_are_rejected(tmp_path, monkeypatch, separator):
    (tmp_path / "README.md").write_text("Z" + chr(58) + separator + "private-data", encoding="utf-8")
    monkeypatch.setattr(validator, "ROOT", tmp_path)
    monkeypatch.setattr(validator, "PACKAGE", tmp_path / "package")
    with pytest.raises(AssertionError, match="private absolute path"):
        validator.validate_no_private_paths()
