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
1. **Standardization & next gate:** time-in-stage, next-gate blocker checklist (5 horizontal reviews matrix + impl report + CR-blocking issues), charter target vs slippage.
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
- **P6 — Registries section** (registry track). *(shipped — see below.)*

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
- **Horizontal review status:** same label parser as specs, but **only for a
  registry with its own repo** (`registry_owns_repo`, i.e. repo named after the
  shortname — currently just MSE Byte Stream Format). Registries that share a
  parent spec's repo (the EME ×3 + WebCodecs ×2) skip the label fetch and read
  `unknown`, because the parent repo's labels describe the *spec*, not the
  registry — inferring from them would misattribute (e.g. show WebCodecs's
  privacy review on the codec registry). The horizontal blocker links to the
  per-registry `review.html?shortname=` tracker for the real status.
- **Entry count:** parse the registry table (row count) from the TR/ED page.
- **Pending registrations** (optional v1): open PRs/issues proposing new entries.
- **Config:** new `registries:` list in `config/specs.yaml` (or a sibling file):
  `shortname, title, parent, tr, repo, hr_shortname`.

### Model / code shape
- `model.py`: `RegistryStage` Literal; `RegistryMeta`, `RegistryStatus`,
  `RegistryView` (stage, next_gate, readiness, horizontal_rows, entry_count,
  pending_count, links). Reuse `HorizontalReviews`.
- `analysis.py`: `registry_next_gate`, a small registry `GATE_REQUIREMENTS`
  (Draft→Snapshot: horizontal reviews resolved; Snapshot→W3C Registry:
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

### Decisions taken (shipped v1)
1. **Placement:** second section on the same page, below the specs ledger. The
   two `table.ledger`s are wired independently in JS (per-table closures over
   their own tbody), so sorting one never reorders the other.
2. **Review column:** first level shows the aggregate `n/5` + colour/glyph mark;
   the panel nests the full 5-group chips under the horizontal blocker (same as
   specs).
3. **Pending registrations:** deferred — the panel links "open PRs" as the
   pending-proposals proxy; entry count is the primary registry signal.

### Follow-ups (not in v1)
- **Entry counts** are config-maintained facts (`entry_count`, verified
  2026-07-16) rather than scraped live; a per-page table-row parser could
  automate them later.
- **"Wide review" is not shown as a blocker.** Its only trackable instance is the
  horizontal reviews (already a blocker); "wide review complete" as a whole is a
  broad WG judgment with no actionable instance, so it was dropped — blockers list
  concrete, handleable items only. **ac_review_done** likewise stays unknown
  (can't be proven from open issues).

---

## P7 — "New this week" activity notifications

**Why:** the dashboard answers *where each spec stands* but not *what just
happened*. Spec work moves slowly, so a single comment is real signal — a chair
needs "what came in since last week" without opening 10 repos. Vendor-neutral
like the rest: no affiliation, no ranking of participants.

### Decisions taken (locked before build)

1. **Badge colour = `--accent` (rust), not rose.** Rose is reserved for
   *bad* (open/blocked/at-risk/overdue) — new discussion is not bad. Accent is
   already defined as *the interactive colour*, and the badge is a click target
   (it expands the row). No new token, no change to the colour contract.
2. **Window = 7 days, computed at build time.** Deterministic, identical for
   every viewer, unit-testable, no client state. Length is one constant
   (`ACTIVITY_WINDOW_DAYS = 7`). The strip states the boundary date explicitly
   ("since 2026-07-28") so "this week" is never ambiguous on a daily-rebuilt page.
   *(Deferred: per-user "since your last visit" via localStorage.)*
3. **Badge counts events; the list dedups to threads.** Each comment = 1, each
   state change = 1 — so the badge is 7 while the list shows 4 rows, each with
   its own count. The strip header reconciles them: "7 updates in 4 threads".
   Same convention as an unread-count over threaded mail.
4. **Panel rows:** drop `Pulse` (verbatim duplicate of the first-level Pulse
   column — the clearest dedup win in the panel); add `New this week` and
   `Oldest open` (`oldest_open_issue_age_days` has been fetched and computed
   since P1 but rendered nowhere); include PR **review** comments; **show comment
   authors**.
5. **Specs only — no badges on registries.** The EME ×3 and WebCodecs ×2
   registries share their parent spec's repo, so repo activity attributed to a
   registry would misattribute — the same reasoning that keeps horizontal-review
   labels off shared-repo registries (P6 above).

**Authors, kept neutral:** GitHub handles only — no avatars, no affiliation, no
"most active" ranking. Muted ink (they're data, not status), capped at 2 + `+N`,
ordered by *first comment in the window* (deterministic and unranked).

### First level — the badge

A filled rust pill with the count, immediately after the title, before the `REC`
badge. Tooltip: `7 updates since 2026-07-28`. Inside the row's click target, so
clicking it expands the panel. **Absent entirely when nothing is new** (per the
meaningful-only rule) — not a `0` pill.

```
    Specification                       Stage   Next     Interop      Pulse
  ─────────────────────────────────────────────────────────────────────────────
  ▸ Media Source Extensions   ❨3❩       CR      →PR ✓    C● F● S●     ● active
    w3c/media-source
  ▸ WebCodecs                 ❨7❩ REC   WD      →CR ✗    C● F◐ S◐     ● quiet 96d
    w3c/webcodecs
  ▸ Autoplay Policy Detection            WD      →CR ·    C○ F○ S○     ● no activity 1913d
    w3c/autoplay                └── no badge: nothing new in the window
```

The count carries the meaning as text, so the signal survives greyscale and
colour-blindness (colour + shape rule).

### Second level — a full-width "New this week" strip

The deduped list needs horizontal room for titles, so it is **not** a
`dl.panel-kv` row inside the 1/3-width Activity group. It spans the panel
(`grid-column: 1 / -1`) above the three existing groups: you clicked the badge,
this is the answer, it comes first. The three groups keep their structure.

```
 ▾ WebCodecs  ❨7❩                       WD      →CR ✗    C● F◐ S◐     ● quiet 12d
 ┌──────────────────────────────────────────────────────────────────────────────────────┐
 │ New this week · 7 updates in 4 threads · since 2026-07-28          all activity ↗    │
 │ ──────────────────────────────────────────────────────────────────────────────────── │
 │  ◇ #812  Clarify VideoFrame colorSpace defaults   3 comments · alice,bob    2d ago   │
 │  ◆ #809  Editorial: fix IDL for AudioDecoderConfig  opened · 1 comment · cd  3d ago  │
 │  ◇ #798  Support for AV1 film grain synthesis     closed                    5d ago   │
 │  ◆ #791  Add codec string for VP9 profile 3       merged · 2 comments · ef   6d ago  │
 │                                                            + 2 more threads ↗        │
 ├──────────────────────────┬──────────────────────────┬────────────────────────────────┤
 │ Standardization & next   │ Interoperability         │ Activity & health              │
 │ Stage          WD        │ Chromium  ● shipped 94   │ New this week  7 (4 threads)   │
 │ Last published 2026-03…  │ Firefox   ◐ partial 130  │ Open issues    42              │
 │ Next gate      → CR  ✗   │ Safari    ◐ partial 16   │ Open PRs       3               │
 │ Blockers to CR           │ All-engines WPT ↗        │ Oldest open    3y 2m    ← new  │
 │  ✘ CR-blocking (2 open)  │ Chromium  118/140        │ Commits  ▁▃▂▅█▂  38 in 6mo     │
 │  ◐ Horizontal 3/5        │ Firefox    92/140        │                                │
 │    a11y ✔resolved  …     │ Safari     74/140        │  (Pulse row dropped — dup)     │
 └──────────────────────────┴──────────────────────────┴────────────────────────────────┘
```

- `◇` issue / `◆` PR, and the state word ("closed"/"merged") — all **muted ink,
  no status colour**. An open issue isn't "bad", so this follows the "registered
  entries are data, not status" precedent rather than inventing issue-state colours.
- Newest first, capped at **8 threads** with an explicit `+ N more ↗` — never a
  silent truncation.
- Title links to the issue/PR; `all activity ↗` →
  `github.com/<repo>/issues?q=sort:updated-desc`.

### Narrow view (designed, not derived)

Below 900px the ledger is already labeled cards and the panel collapses to one
column, so the strip must be authored for that width — see
`docs/ux-visual-rules.md` § Responsive layout.

```
  ≤900px — collapsed card                ≤900px — expanded (panel = 1 column)
  ┌────────────────────────────────┐     ┌────────────────────────────────┐
  │ ▸ WebCodecs ❨7❩          WD    │     │ New this week · 7 updates in   │
  │   w3c/webcodecs                │     │ 4 threads · since 2026-07-28   │
  │   NEXT GATE   →CR ✗            │     │ all activity ↗                 │ ← link wraps
  │   INTEROP     C● F◐ S◐         │     │ ────────────────────────────── │   to own line
  │   PULSE       ● quiet 12d      │     │ ◇ #812 Clarify VideoFrame      │
  └────────────────────────────────┘     │        colorSpace defaults     │ ← title wraps
    badge stays inline with the title,   │        3 comments · alice,bob  │ ← meta drops
    nowrap on the pill itself so it      │        · 2d ago                │   below, left
    wraps *with* the last word, never    │ ◆ #809 Editorial: fix IDL for  │
    alone; never shrinks the title       │        AudioDecoderConfig      │
    column (col 2 is minmax(0,1fr))      │        opened · 1 comment      │
                                         │ + 2 more threads ↗             │ ← left, not right
                                         └────────────────────────────────┘
```

Concrete narrow requirements:

- Strip row is a grid: `minmax(0, 1fr) max-content max-content` wide →
  **single column** narrow, with `summary · authors · ago` as a muted meta line
  beneath the title. `minmax(0, …)`, never a bare `1fr`, so a long title cannot
  force horizontal scroll.
- Issue titles get `overflow-wrap: anywhere` (IDL names and long identifiers are
  common) and **never** `white-space: nowrap`. `nowrap` applies only to the count
  pill, `#812`, and `2d ago`.
- Strip header `flex-wrap: wrap` so `all activity ↗` drops to its own line
  instead of squeezing the title (same pattern as `.section-head`).
- `+ N more ↗` is right-aligned wide, **left-aligned** in the stacked layout.
- Authors are the lowest-signal element: capped at 2 + `+N` at every width, and
  allowed to wrap onto the meta line rather than being hidden (hiding facts by
  viewport would make narrow lie).
- Verified at all six tiers with a panel expanded, per the Dev Loop's Step 4.

### Data sources (2 extra calls per repo, +1 for PR review comments)

~10 distinct repos × 3 calls/day is negligible against the daily refresh.

| Call | Gives |
|---|---|
| `issues?state=all&sort=updated&direction=desc&since=T` | threads touched in the window + **titles**, state, issue-vs-PR, `created_at`, `closed_at`, `pull_request.merged_at` |
| `issues/comments?since=T` | one entry per comment on issues **and PR conversations**, with `issue_url` + `user.login` + `created_at` |
| `pulls/comments?since=T` | inline PR **review** comments (decision 4) |

- The comments endpoints carry no title, which is why the issues listing is also
  needed. Any commented thread necessarily appears there — a comment bumps
  `updated_at`. Both use `state=all`; the default `state=open` would silently
  drop closed-this-week threads.
- Events counted: `comment` (1 each), `opened`, `closed`, `merged`.
  **`reopened` is not detectable** without the events API — a documented
  limitation, not worth a per-issue call.
- **Fetch failure** follows the existing policy: `activity` becomes a
  `merge_spec` last-known-good key. Events are stored **with timestamps**, so a
  stale list self-decays when re-filtered against the fresh window. Failure with
  no last-good ⇒ no badge and `—` in the panel, never `0` (unknown ≠ zero).

### Code shape

```
model.py      + ActivityKind = Literal["issue", "pr"]
              + ActivityEvent(number, kind, title, url, state, event, author, at)
              + SpecActivity(window_days, events, known: bool)   → Spec.activity
              + ActivityThread(number, kind, title, url, state, event_count,
                               summary, authors, days_ago)
              + SpecView.activity_threads / activity_count / activity_overflow
activity.py   NEW, pure: group_activity(events, since, now, limit) -> threads
                        thread_summary(events) -> "opened · 3 comments"
                        format_authors(events, cap=2) -> "alice, bob +1"
                        format_ago(days) -> "2d ago"
fetch/github.py  I/O:   fetch_updated_issues / fetch_issue_comments /
                        fetch_review_comments  (reuse _fetch_all_pages + github_get)
                 pure:  extract_state_events(issues, since)
                        extract_comment_events(comments, title_index, since)
assemble.py   build_spec(…, updated_issues, comments, review_comments) -> SpecActivity
              merge_spec: new "activity" failure key
render.py     ACTIVITY_WINDOW_DAYS; pass the window boundary date to the template
template      badge macro · activity_strip macro · reworked Activity & health group
              · CSS incl. the narrow rules above
```

### Sub-phases (each a full Dev Loop pass)

- **P7a** — model types + `activity.py` + the pure extractors + full unit tests.
  No network, no UI.
- **P7b** — the three fetchers, `build_spec`/`merge_spec` wiring, last-good
  fallback, mocked-I/O tests.
- **P7c** — badge + strip + Activity & health rework + CSS (wide **and** narrow),
  render tests, Step 4 responsive check at all six tiers,
  `/mediawg-dashboard-ux-review`, then update `docs/ux-visual-rules.md` (badge
  row: accent pill = new-activity count, interactive) and `README.md`.

### Adjustments made during the build (P7 shipped)

The five decisions above held. These came out of the review + responsive passes:

1. **`+ N more threads` is non-interactive text**, not a link — it would have
   pointed at exactly the same URL as `all activity ↗` in the strip header, and
   each link appears once. Still always shown (no silent truncation). Follows the
   `REC` tail badge's precedent.
2. **The thread breakdown lives only in the strip header.** The Activity & health
   row carries the bare count; "New this week 24 in 12 threads" beside
   "24 updates in 12 threads" was the same fact twice in one panel. Aggregate
   here / detail there — the horizontal-blocker-vs-chips split.
3. **The strip header drops "in N threads" when it equals the update count** —
   "2 updates in 2 threads" repeats the first number (meaningful-only).
4. **`ActivityThread.state` was dropped.** Nothing rendered it: the row shows
   `summary` (what happened *in the window*), so a thread's current open/closed
   state was a stored-but-unrendered field.
5. **Threads sort on the newest event's timestamp**, not `days_ago` — the latter
   is day-granular, so same-day threads were tie-breaking on issue number and
   listing the older thread first.
6. **`ACTIVITY_WINDOW_DAYS` lives in `model.py`** (re-exported by `activity.py`)
   so the stored `SpecActivity.window_days` default can't drift from the window
   the fetchers and view actually use.
7. **`Spec.activity` is defaulted, not required** — `laststate.py` drops entries
   that fail validation, so a required new field would have silently wiped the
   whole last-known-good store on the first refresh after deploy, exactly when
   the fallback matters most. Guarded by a test.

### P7 follow-up — Pulse contradicted the badge

Shipping P7 exposed a pre-existing definition bug: `days_since_activity` was
**commits only**, so Media Source Extensions rendered "no activity 272d" next to
a "2 new" badge. Three specs were mislabeled.

- **"Activity" now means commits *or* discussion**, whichever is more recent
  (`activity.combined_activity_days`). `SpecHealth.days_since_activity` was
  renamed to **`days_since_commit`** so the field stops lying, and the two raw
  facts stay separate — each restorable under its own last-good failure key —
  with the combination derived in the pure view layer.
- Discussion recency needs an **unbounded** signal (a comment 30 days ago is
  still activity but produces no badge), so `fetch_last_discussion` asks for the
  single most-recently-updated thread with **no `since`** — one extra call/repo.
  It lands on `SpecActivity.last_discussion_days`, inside the existing `activity`
  failure key, so last-known-good needed no new branch.
- **Sorting was alphabetical.** Every `<th>` gets a handler, but the comparator
  read cell *text*: Pulse ordered "active" < "blocker open 2309d" < "no activity
  272d"; Interop sorted `C●F◐S○`; the registries' Review sorted `"0/5"` → `0` for
  every row. Fixed generally with `data-sort` (preferred by the JS) rather than
  per-column special cases — and Interop/Pulse gained the `⇅` glyph they'd been
  missing while already being clickable.
- Pulse sorts on **recency, not tier**: a spec with a decade-old blocker and
  three comments this week is genuinely more current than a silent one.
</content>
