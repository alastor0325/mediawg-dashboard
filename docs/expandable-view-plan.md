# Plan — Expandable per-spec view

Approved design (this doc = the build plan). The dashboard stays **vendor-neutral** (see the memory rule): no vendor stance, engines shown evenly, personal judgment stays out of the product.

## Goal
Click a spec row → expand a detail panel. Add a first-level row that fuses **maturity** and **shipping reality**, and a second-level panel that explains **why / since when / what's blocking**.

## First level (collapsed row)
Name + 4 encoded columns (each a chip/dot/mini-bar, scannable vertically):
- **STAGE** — ordinal chip (exists today).
- **NEXT** — next gate (`→CR`/`→PR`) + `○ ready / ● blocked` dot.
- **INTEROP** — 3 engine dots (alphabetical C/F/S: `● ship ◐ partial ○ none`) + all-engines WPT %.
- **PULSE** — health dot (`● on-track / ◍ watch / ⚠ at-risk`) + short reason (stage-age / activity / oldest blocker).
Plus a roll-up header line (e.g. `REC 0 · CR 0 · WD/FPWD 8 · ED 1 · shipping cross-engine N/9`).

## Second level (expand panel) — 3 groups
1. **Standardization & next gate:** time-in-stage, next-gate blocker checklist (wide review + 5 horizontal reviews matrix + impl report + CR-blocking issues), charter target vs slippage.
2. **Interoperability:** per-engine WPT % + counts, test-coverage depth, versions shipped, Interop focus-area, top gaps.
3. **Activity & health:** why-this-pulse, oldest unresolved blocking item, backlog trend, agenda count, editor count, links.

(Full ASCII of both levels is in the meeting/design discussion; this plan is the build spec.)

## Data sources
- **Available now:** stage + last-TR date + ED url (W3C API); issues/PRs/oldest-issue (GitHub) — already fetched.
- **New plumbing:** wpt.fyi (all-engines + per-engine pass %, test count); browser support per engine (BCD/webstatus.dev); GitHub **label queries** (horizontal-review `*-tracker`/`*-needs-resolution`, blocking issues, `agenda` count, oldest blocking item); commit recency + editor count; **charter targets + non-derivable process facts** in `config/specs.yaml`; **daily snapshots** for trends.

## Design rules
- All computation is **pure functions** (new `analysis.py`) with unit tests; fetchers/template stay thin. Unknown inputs degrade gracefully (`unknown`/`—`), never crash.
- Neutral: per-engine data alphabetical + even; no "outlier"/stance fields.

## Phased tasks
- **P1 — Pure computation core** (no network): model types (`SpecMilestones`, `HorizontalReviews`, `InteropStatus`, `Blocker`, `Pulse`) + `analysis.py` (`next_gate`, `gate_requirements`, `compute_blockers`, `compute_stage_age_days`, `support_glyph`/`interop_label`, `compute_pulse`) + full unit tests. **← start here.**
- **P2 — First-level UI:** render STAGE/NEXT/INTEROP/PULSE columns + roll-up header from the computed view; tests on HTML marks; keep mobile card layout working.
- **P3 — Expand panel UI:** `<details>`-based progressive disclosure, the 3 groups; tests.
- **P4 — Fetchers:** wpt.fyi + browser-support + GitHub label queries + config charter/process facts; unit tests mock I/O.
- **P5 — Trends + wire-up:** daily snapshot persistence (backlog/WPT deltas), wire fetchers into `cmd_refresh`, update README.

Each task runs the full mediawg-dashboard Dev Loop (pure fns → tests → /simplify → commit+push).
</content>
