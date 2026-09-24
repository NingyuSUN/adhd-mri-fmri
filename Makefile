.PHONY: quickstart test validate-public syntax

PYTHON ?= python3
OUTPUT_DIR ?= artifacts/quickstart

quickstart:
	$(PYTHON) tools/quickstart.py --output-dir $(OUTPUT_DIR)

test:
	$(PYTHON) -m pytest reproduction/tests -q

validate-public:
	$(PYTHON) tools/validate_public_artifacts.py

syntax:
	$(PYTHON) -c 'import ast; from pathlib import Path; files=list(Path("reproduction").rglob("*.py"))+list(Path("reporting").rglob("*.py"))+list(Path("tools").rglob("*.py")); [ast.parse(p.read_text(encoding="utf-8"), filename=str(p)) for p in files]; print(f"parsed {len(files)} Python files")'
