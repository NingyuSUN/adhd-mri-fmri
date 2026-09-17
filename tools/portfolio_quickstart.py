#!/usr/bin/env python3
"""Run a five-minute, aggregate-only portfolio smoke test.

This command intentionally does not need ADHD-200 data, model checkpoints, or
scientific Python dependencies. It reads committed summary CSVs and produces a
small report that a reviewer can reproduce after cloning the repo.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "results" / "tables_figures_20260914" / "tables"
TABLE2 = TABLE_DIR / "Table2_primary_model_performance.csv"
TABLE3 = TABLE_DIR / "Table3_primary_contrast_by_QC.csv"


def read_csv(path: Path, required: Iterable[str]) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"required aggregate file is missing: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"aggregate file is empty: {path}")
    missing = set(required) - set(rows[0])
    if missing:
        raise ValueError(f"{path.name} is missing columns: {sorted(missing)}")
    return rows


def _float(value: str) -> float:
    return float(value.strip().replace("+", ""))


def build_summary(root: Path = ROOT) -> dict:
    table_dir = root / "results" / "tables_figures_20260914" / "tables"
    models = read_csv(
        table_dir / "Table2_primary_model_performance.csv",
        ("Model", "CV mean fold AUC", "LOSO within-site pair-weighted AUC", "LOSO equal-site macro AUC"),
    )
    contrasts = read_csv(
        table_dir / "Table3_primary_contrast_by_QC.csv",
        ("Framework", "Cohort", "Delta AUC", "90% interval", "Uncertainty method"),
    )
    by_model = {
        row["Model"]: {
            "cv_mean_fold_auc": _float(row["CV mean fold AUC"]),
            "loso_pair_weighted_auc": _float(row["LOSO within-site pair-weighted AUC"]),
            "loso_equal_site_macro_auc": _float(row["LOSO equal-site macro AUC"]),
        }
        for row in models
    }
    primary_cv = next(row for row in contrasts if (row["Framework"], row["Cohort"]) == ("CV", "primary"))
    primary_loso = next(row for row in contrasts if (row["Framework"], row["Cohort"]) == ("LOSO", "primary"))
    return {
        "schema_version": "portfolio-quickstart.v1",
        "data_scope": "aggregate-only; no raw MRI or subject-level predictions",
        "source": "results/tables_figures_20260914/tables/Table2_primary_model_performance.csv + Table3_primary_contrast_by_QC.csv",
        "models": by_model,
        "primary_contrast": {
            "cv_delta_auc": _float(primary_cv["Delta AUC"]),
            "cv_interval": primary_cv["90% interval"],
            "loso_delta_auc": _float(primary_loso["Delta AUC"]),
            "loso_interval": primary_loso["90% interval"],
        },
        "checks": {
            "model_rows": len(models),
            "contrast_rows": len(contrasts),
            "required_sources_present": True,
        },
        "interpretation": "The confound baseline remains strong, while the structural increment is not stable across QC cohorts and evaluation frameworks.",
    }


def render_markdown(summary: dict) -> str:
    models = summary["models"]
    contrast = summary["primary_contrast"]
    lines = [
        "# ADHD-200 portfolio quickstart",
        "",
        "This report was generated from committed aggregate CSVs. It does not access raw MRI, subject-level predictions, or model checkpoints.",
        "",
        "## Primary aggregate check",
        "",
        f"- CV structural increment: **{contrast['cv_delta_auc']:+.4f} AUC**, {contrast['cv_interval']}.",
        f"- LOSO structural increment: **{contrast['loso_delta_auc']:+.4f} AUC**, {contrast['loso_interval']}.",
        "",
        "## Model summary",
        "",
        "| Model | CV mean fold AUC | LOSO pair-weighted AUC | LOSO equal-site macro AUC |",
        "|---|---:|---:|---:|",
    ]
    for name in sorted(models):
        row = models[name]
        lines.append(
            f"| `{name}` | {row['cv_mean_fold_auc']:.4f} | {row['loso_pair_weighted_auc']:.4f} | {row['loso_equal_site_macro_auc']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Engineering boundary",
            "",
            summary["interpretation"],
            "This is a research benchmark, not a clinical diagnostic output.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(output_dir: Path, summary: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "summary.md").write_text(render_markdown(summary), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts" / "portfolio_quickstart")
    parser.add_argument("--check", action="store_true", help="validate sources without writing output files")
    args = parser.parse_args(argv)
    summary = build_summary()
    if args.check:
        print(json.dumps({"status": "pass", "schema_version": summary["schema_version"], "models": len(summary["models"])}, sort_keys=True))
        return 0
    write_report(args.output_dir, summary)
    print(json.dumps({"status": "pass", "output_dir": str(args.output_dir), "models": len(summary["models"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
