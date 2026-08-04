# mediawg-dashboard Dev Loop

The **mediawg-dashboard Dev Loop** is a mandatory workflow for all code changes. All steps are required and cannot be skipped.

## The Cycle

Development proceeds through seven sequential steps: understand the task, extract & develop, write tests, responsive check, agent review, commit & push, then conclude.

## Core Requirements

- All new or changed logic must be extracted into **pure/testable functions** (no I/O, no network calls) so they can be unit tested directly.
- Every function added or changed must have **unit tests** covering its branches. If behavior is removed, a test must assert the removal holds.
- **`pytest tests/unit/` must pass** before committing. Failing tests are a hard blocker — fix them, do not work around them.
- **Every UI change must be checked at all breakpoints** (Step 4). The narrow/card layout is a first-class layout, not an afterthought — a change that only reads well wide is incomplete.
- **README.md must be updated** whenever a command is added/removed or a flag/default changes.
- Unit tests go in `tests/unit/`, mock all I/O and network calls.
- Integration tests go in `tests/integration/` (only for changes touching real I/O or APIs).
- Write the failing test first — confirm it fails before implementing.

## Process Details

### Step 1 — Understand
Read the relevant source files before touching anything. Understand the existing structure: which functions are involved, what tests already cover them.

### Step 2 — Extract & Develop
Write the implementation. Extract logic into named pure functions first, then call them from handlers/controllers. Keep entry points thin — they only wire up I/O and call pure functions.

### Step 3 — Write Tests
For every function added or changed, write unit tests:
- Happy path
- Each meaningful branch or flag
- Regression guards for removed behavior

Run and confirm green:
```
pytest tests/unit/
```

### Step 4 — Responsive Check
**Required for any change touching `templates/index.html.j2`, `render.py`, or the
view layer in `analysis.py`.** Skip only for pure non-UI changes (fetchers,
config parsing, snapshot plumbing).

The stylesheet defines five tiers — the ledger stops being a table below 900px
and becomes labeled cards, so a wide-only check proves nothing about half the
layouts. Render (`make refresh`, or build from a fixture) and verify each:

| Viewport | Tier | What must hold |
|---|---|---|
| 1440×900 | full desktop | intended design; panel is 3-up |
| 1100×800 | laptop | tightened padding; nothing clipped by the narrower `col-*` widths |
| 900×800 | tablet → **cards** | `thead` hidden, each row a labeled card; every cell's `data-label` present and correct |
| 640×900 | phone | labels + values still aligned; long titles wrap, don't overflow |
| 420×800 | very narrow | summary single-column; no horizontal scrollbar |
| 900×500 | landscape phone | compressed masthead still readable |

Check with the `playwright` skill (screenshot each width **with a panel expanded** —
the panel is the densest content), and assert no horizontal overflow:

```js
document.documentElement.scrollWidth <= window.innerWidth   // must be true
```

The invariants a UI change must not break (no overflow, no `nowrap` on
user-length text, `data-label` on every first-level cell, right-aligned→left in
cards, …) live in **`docs/ux-visual-rules.md` § Responsive layout** — read it
before changing layout, and add to it if the change establishes a new rule. Most
are cheap to also assert in `tests/unit/test_render.py` as string checks on the
rendered CSS/HTML.

### Step 5 — Agent Review
Run `/simplify` to have a fresh-context agent review the changes for code quality, reuse, and efficiency. Apply any fixes before committing.
For UI changes also run `/mediawg-dashboard-ux-review` (visual rules + responsive). Apply any fixes before committing.

### Step 6 — Commit & Push
```
git commit -m "<type>: <what and why>"
git push
```
Both are required. Never commit without pushing.

### Step 7 — Conclude
Summarize: what changed, what tests were added, whether the responsive check passed at every tier, and whether README was updated.
