"""The README headline table must agree with docs/RESULTS.md and the summaries."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUMMARIES = ["docs/RESULTS.md", "docs/MODEL_CARD.md", "docs/FINAL_REPORT.md", "docs/CASE_STUDY.md"]


def headline_rows():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    section = text.split("## Main findings", 1)[1].split("\n## ", 1)[0]
    rows = []
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 3 and re.match(r"^0\.\d{3}", cells[2]):
            rows.append((cells[0], cells[1], re.findall(r"0\.\d{3}", cells[2])))
    return section, rows


def test_readme_headline_table_is_parsed():
    _, rows = headline_rows()
    assert len(rows) == 4


def test_headline_values_match_results():
    results = (ROOT / "docs/RESULTS.md").read_text(encoding="utf-8")
    for evaluation, features, values in headline_rows()[1]:
        for value in values:
            assert value in results, f"{evaluation} / {features}: {value} missing from docs/RESULTS.md"


def test_headline_points_appear_in_every_summary():
    for path in SUMMARIES:
        text = (ROOT / path).read_text(encoding="utf-8")
        for evaluation, features, values in headline_rows()[1]:
            assert values[0] in text, f"{evaluation} / {features}: {values[0]} missing from {path}"


def test_benchmark_size_is_consistent():
    section, _ = headline_rows()
    size = re.search(r"(\d+)-subject benchmark", section).group(1)
    for path in SUMMARIES:
        assert size in (ROOT / path).read_text(encoding="utf-8"), f"{size} missing from {path}"
