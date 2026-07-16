# mediawg-dashboard

Read-only, **vendor-neutral** status dashboard for the W3C Media Working Group.
Consolidates each spec's Rec-track stage, next-gate readiness, cross-engine
interop, and health into one daily-refreshed view, with a click-to-expand detail
panel per spec.

## Status

Expandable per-spec view implemented (`make refresh` fetches live data and
renders `output/index.html`). Each row shows **Stage · Next-gate · Interop
(neutral C/F/S tri-dot + all-engines WPT %) · Pulse**, plus a roll-up of how
many specs ship cross-engine. Clicking a spec expands three groups:
Standardization & next gate (stage age, blocker checklist, horizontal-review
matrix, charter target vs slippage), Interoperability (per-engine support, WPT,
coverage), and Activity & health (pulse, oldest blocking issue, issues/PRs,
agenda/editors, backlog trend, links).

A second **Registries** ledger (registry track, Process §6.5) sits below the
specs table: each of the 6 MediaWG registries shows **Stage · Next-gate
(→ Candidate Snapshot) · horizontal Review (n/5) · Entries**, expanding to a
two-group panel (Registry & next gate with the blocker checklist + 5 review
chips; Table with entry count / pending). It shares the specs' stage/gate/review
model but drops the interop/WPT/pulse axes (a registry documents values, it
isn't shipped or tested). The two tables are fully independent — sorting one
never reorders the other.

Data sources: W3C API (stage/dates, incl. registry status), GitHub API (issues,
labels → horizontal reviews + agenda + blocking, commits → activity/editors),
wpt.fyi (interop test scores), webstatus.dev (per-engine support), and neutral
config facts (charter targets + registry entry counts in `config/specs.yaml`).
Any single source failing degrades that field to "unknown" rather than aborting
the refresh.

Design notes and phase plan: `docs/expandable-view-plan.md`,
`docs/spec-process-flow.md`, `docs/spec-inventory.md`.

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
config/specs.yaml        The 9 MediaWG specs + 6 registries tracked
templates/               Jinja2 templates (empty in Phase 0)
tests/unit/              Unit tests, mock all I/O
tests/integration/       Integration tests (real I/O), if any
output/                  Rendered HTML (gitignored)
data/cache/              API response cache (gitignored)
data/history.json        Daily snapshots for trend signals (gitignored)
data/annotations.yaml    Optional personal layer (gitignored)
```

## Dev flow

All code changes follow the **mediawg-dashboard Dev Loop** in `.claude/skills/mediawg-dashboard-dev/skill.md`.

## License

Not yet licensed. Will be decided if/when upstream contribution becomes a real prospect.
