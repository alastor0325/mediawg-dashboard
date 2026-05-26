.PHONY: refresh brief test clean install help

help:
	@echo "Targets:"
	@echo "  install  Create .venv and install deps via uv"
	@echo "  refresh  Fetch data and render the dashboard"
	@echo "  brief    Print the terminal morning brief"
	@echo "  test     Run unit tests"
	@echo "  clean    Remove generated output and caches"

install:
	@if command -v uv >/dev/null 2>&1; then \
	  uv venv && uv pip install -e ".[dev]"; \
	else \
	  python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"; \
	fi

PYTHON ?= .venv/bin/python
PYTEST ?= .venv/bin/pytest

refresh:
	@$(PYTHON) -m mediawg_dashboard.cli refresh

brief:
	@$(PYTHON) -m mediawg_dashboard.cli brief

test:
	@$(PYTEST) tests/unit/

clean:
	rm -rf output/ data/cache/ .pytest_cache/ src/*.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
