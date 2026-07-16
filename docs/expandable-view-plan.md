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
- **P5 — Trends + wire-up:** daily snapshot persistence (backlog/WPT deltas), wire fetchers into `cmd_refresh`, update README. *(P1–P5 shipped.)*
- **P6 — Registries section** (registry track). *← proposed; see below.*

Each task runs the full mediawg-dashboard Dev Loop (pure fns → tests → /simplify → commit+push).

---

## P6 — Registries section (Registry Track)

**Why:** the WG maintains 6 registries on the **Registry Track** — a separate,
simpler lifecycle than the Rec track, with a *different* gate and *no* interop
axis. They don't fit the specs table. A dedicated section lets a co-chair track
the wide-review push that advances Registry Draft → Candidate Registry Snapshot
(the process François kicked off 2026-07-16). Vendor-neutral like the rest.

### The 6 registries (all currently Registry Draft, verified)
| Registry | Parent | shortname |
|---|---|---|
| MSE Byte Stream Format | MSE | mse-byte-stream-format-registry |
| EME Initialization Data Format | EME | eme-initdata-registry |
| EME Stream Format | EME | eme-stream-registry |
| EME HDCP Version | EME | eme-hdcp-version-registry |
| WebCodecs Codec | WebCodecs | webcodecs-codec-registry |
| WebCodecs VideoFrame Metadata | WebCodecs | webcodecs-video-frame-metadata-registry |

### Registry Track model (Process §6.5.2 — verified)
Parallel to Rec track but simpler:
`Registry Draft → Candidate Registry Snapshot (+ Candidate Registry Draft) → W3C Registry`.
Gates: **Draft → Candidate Snapshot = wide/horizontal review** (the current one);
**Candidate Snapshot → W3C Registry = AC review**. **No implementation /
interop / WPT gate** — registries document values, they aren't shipped or tested.

### What to show (and what NOT to)
First-level row per registry: **Registry · Parent · Stage · Next-gate
(→ Candidate Snapshot, ready/blocked) · Review (5-group horizontal status) ·
Entries**. Expand → per-group review breakdown (linked to tracker/request repos),
parent spec, last published, entry count + pending registrations, links.
- **Shares with specs:** Stage chip, Next-gate readiness, horizontal-review
  chips + `hr_review_url`/`horizontal_group_url` links, the aligned key/value
  panel, and the neutral colour+icon system.
- **Drops (N/A for registries):** Interop tri-dot, per-engine WPT, browser
  support, shipping roll-up, Pulse.
- **Adds:** a `RegistryStage` enum, and **Entries / Pending registrations** as
  the registry-specific "living" signal (a Candidate Snapshot stabilises entry
  *requirements*, not entries — the table keeps growing).

### Data sources
- **Stage + last-published:** W3C API (`/specifications/<shortname>/versions/latest`),
  mapping registry statuses → `RegistryStage`.
- **Horizontal review status:** same as specs — in-repo `*-tracker`/
  `*-needs-resolution` labels and the per-spec `review.html?shortname=` tracker
  (resolve each registry's tracker shortname; the EME/MSE ones share their
  parent's repo, so labels may live on the parent repo — confirm per registry).
- **Entry count:** parse the registry table (row count) from the TR/ED page.
- **Pending registrations** (optional v1): open PRs/issues proposing new entries.
- **Config:** new `registries:` list in `config/specs.yaml` (or a sibling file):
  `shortname, title, parent, tr, repo, hr_shortname`.

### Model / code shape
- `model.py`: `RegistryStage` Literal; `RegistryMeta`, `RegistryStatus`,
  `RegistryView` (stage, next_gate, readiness, horizontal_rows, entry_count,
  pending_count, links). Reuse `HorizontalReviews`.
- `analysis.py`: `registry_next_gate`, a small registry `GATE_REQUIREMENTS`
  (Draft→Snapshot: wide review + horizontal resolved; Snapshot→W3C Registry:
  AC review), `registry_view(...)` — all pure, tested. Reuse `_readiness`,
  `horizontal_summary`, `readiness_glyph`.
- `config.py`: parse `registries:`. `assemble.py`: `build_registry(...)` pure.
- `render.py`: build registry rows; template: a **"Registries" section below the
  specs ledger** (a second `<table class="ledger">` with a `col`-group sized for
  its columns). *(Placement: second section on the same page — TBD vs a tab.)*
- `fetch/`: registry stage (reuse `fetch_spec_status`), horizontal labels
  (reuse), entry-count parser (new, pure + tested with a saved HTML fixture).

### Sub-phases (each through the Dev Loop)
- **P6a** — registry model + `analysis` (pure) + `config` for the 6 + tests.
- **P6b** — fetchers (stage, horizontal, entry-count) + `build_registry` + tests.
- **P6c** — render the Registries section + tests; refresh + deploy.

### Open questions (for confirmation before P6a)
1. **Placement:** second section on the same page (recommended) vs a Specs/Registries tab.
2. **Review column:** full 5-group chips (consistent with specs) vs a single
   "wide review: requested/in-progress/done" state.
3. **Pending registrations:** include in v1, or defer (entry count only)?
</content>
