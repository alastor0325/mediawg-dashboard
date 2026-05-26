# mediawg-dashboard

Read-only status dashboard for the W3C Media Working Group. Consolidates spec stage, horizontal review state, open issues, and recent meeting outcomes across the 9 MediaWG specs into one daily-refreshed view.

## Status

Phase 0 — scaffolding only. `make refresh` runs but does nothing useful yet.

## Quick start

```sh
make install       # creates .venv and installs deps via uv
make refresh       # fetches data and renders the dashboard (no-op in Phase 0)
make brief         # prints the morning brief (no-op in Phase 0)
make test          # runs unit tests
make clean         # removes generated output and caches
```

## Layout

```
src/mediawg_dashboard/   Python package
config/specs.yaml        The 9 MediaWG specs tracked
templates/               Jinja2 templates (empty in Phase 0)
tests/unit/              Unit tests, mock all I/O
tests/integration/       Integration tests (real I/O), if any
output/                  Rendered HTML (gitignored)
data/cache/              API response cache (gitignored)
data/annotations.yaml    Optional personal layer (gitignored)
```

## Dev flow

All code changes follow the **mediawg-dashboard Dev Loop** in `.claude/skills/mediawg-dashboard-dev/skill.md`.

## License

Not yet licensed. Will be decided if/when upstream contribution becomes a real prospect.
