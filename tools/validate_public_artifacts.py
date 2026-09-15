#!/usr/bin/env python3
"""Validate the public, aggregate-only evidence contract."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "results" / "tables_figures_20260914"
FORBIDDEN = ("/home/", "/mnt/", "/Users/", "/content/")
WINDOWS_ABSOLUTE_PATH = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]")
FORBIDDEN_COLUMNS = {"subject_id", "participant_id", "t1_path_original", "prediction", "score"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_manifest() -> int:
    manifest = json.loads((PACKAGE / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        path = PACKAGE / item["path"]
        if not path.is_file():
            raise AssertionError(f"manifest file is missing: {item['path']}")
        if path.stat().st_size != item["bytes"]:
            raise AssertionError(f"manifest byte count mismatch: {item['path']}")
        if sha256(path) != item["sha256"]:
            raise AssertionError(f"manifest hash mismatch: {item['path']}")
    return len(manifest["files"])


def validate_tables() -> int:
    tables = sorted((PACKAGE / "tables").glob("*.csv"))
    if len(tables) != 14:
        raise AssertionError(f"expected 14 aggregate tables, found {len(tables)}")
    for path in tables:
        with path.open(newline="", encoding="utf-8") as handle:
            header = set(next(csv.reader(handle)))
        forbidden = header & FORBIDDEN_COLUMNS
        if forbidden:
            raise AssertionError(f"individual-level columns in {path.name}: {sorted(forbidden)}")
    return len(tables)


def validate_figures() -> tuple[int, int]:
    pngs = sorted((PACKAGE / "figures").glob("*.png"))
    pdfs = sorted((PACKAGE / "figures").glob("*.pdf"))
    if len(pngs) != 9 or len(pdfs) != 8:
        raise AssertionError(f"expected 9 PNG and 8 PDF figures, found {len(pngs)} PNG and {len(pdfs)} PDF")
    return len(pngs), len(pdfs)


def validate_no_notebooks() -> int:
    notebooks = sorted(ROOT.rglob("*.ipynb"))
    if notebooks:
        relpaths = [str(path.relative_to(ROOT)) for path in notebooks]
        raise AssertionError(f"notebooks are not part of the final package: {relpaths}")
    retired_files = sorted(path for path in (ROOT / "notebooks").rglob("*") if path.is_file())
    if retired_files:
        relpaths = [str(path.relative_to(ROOT)) for path in retired_files]
        raise AssertionError(f"retired notebook-era files are present: {relpaths}")
    return 0


def validate_no_private_paths() -> int:
    checked = 0
    roots = [
        ROOT / "README.md",
        ROOT / "PROJECT_STATUS.md",
        ROOT / "PORTFOLIO_CASE_STUDY.md",
        ROOT / "docs",
        ROOT / "reporting",
        ROOT / "reproduction",
        ROOT / "tools",
        ROOT / "demo",
        PACKAGE,
    ]
    for root in roots:
        paths = [root] if root.is_file() else root.rglob("*")
        for path in paths:
            if (
                not path.is_file()
                or path.resolve() == Path(__file__).resolve()
                # Vendored third-party sources have their own frozen hash manifest.
                or path.is_relative_to(ROOT / "reproduction" / "legacy" / "vendor")
                # Imports during tests cache this validator's forbidden tokens.
                # Bytecode is generated binary data, not public source text.
                or path.suffix.lower() in {".png", ".pdf", ".pyc", ".pyo"}
            ):
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if any(token in text for token in FORBIDDEN) or WINDOWS_ABSOLUTE_PATH.search(text):
                raise AssertionError(f"private absolute path in public file: {path}")
            checked += 1
    return checked


def main() -> int:
    manifest_files = validate_manifest()
    table_count = validate_tables()
    png_count, pdf_count = validate_figures()
    notebook_count = validate_no_notebooks()
    checked_files = validate_no_private_paths()
    result = {
        "status": "pass",
        "manifest_files": manifest_files,
        "aggregate_tables": table_count,
        "figure_png": png_count,
        "figure_pdf": pdf_count,
        "notebook_files": notebook_count,
        "path_checked_files": checked_files,
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
