.PHONY: refresh brief test clean install help

help:
	@echo "Targets:"
	@echo "  install  Create .venv and install deps via uv"
	@echo "  refresh  Fetch data and render the dashboard"
	@echo "  brief    Print the terminal morning brief"
	@echo "  test     Run unit tests"
	@echo "  clean    Remove generated output and caches"

install:
	uv venv
	uv pip install -e ".[dev]"

refresh:
	@PYTHONPATH=src python -m mediawg_dashboard.cli refresh

brief:
	@PYTHONPATH=src python -m mediawg_dashboard.cli brief

test:
	@PYTHONPATH=src pytest tests/unit/

clean:
	rm -rf output/ data/cache/ .pytest_cache/ src/*.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
