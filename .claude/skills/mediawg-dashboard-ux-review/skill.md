---
name: mediawg-dashboard-ux-review
description: >
  Review the mediawg-dashboard UI for visual consistency against
  docs/ux-visual-rules.md — colour semantics, colour+shape icons, neutrality,
  dedup, and responsive layout. Run after any change to templates/index.html.j2
  or the render/analysis view layer, or on request ("ux review the dashboard").
---

# mediawg-dashboard UX review

Check the dashboard's UI against its own visual rules and report inconsistencies.
This is a **review** skill (like /simplify) — it finds and reports; apply fixes
after.

## Step 1 — Load the rules & the UI

Read `docs/ux-visual-rules.md` (the source of truth) and `templates/index.html.j2`.
If a rendered `output/index.html` exists, skim it too (real values surface
issues templates hide). The visual-rule summary you're enforcing:

- **Colour = one meaning:** green good/done/shipped/ready/on-track/resolved ·
  amber caution/partial/requested/watch · red bad/none/open/blocked/at-risk/
  overdue · grey unknown/N-A · blue = CR stage pip only · **accent (rust) =
  interactive only, never status**.
- **Colour + shape:** every status has a distinct glyph AND colour (survives
  grеyscale / colour-blindness). Flag any colour-only or shape-only signal.
- **Neutrality:** engines always alphabetical Chromium / Firefox / Safari, equal
  weight; no logos, no "reference"/"outlier" language.
- **Dedup:** each fact and each link appears once. Horizontal review is a blocker
  line with the 5 groups nested beneath it — not a separate section.
- **Meaningful-only:** don't show a signal that can't mean anything yet (e.g.
  backlog trend with <2 snapshots; "behind charter" only when overdue).
- **Aligned & responsive:** panel groups are aligned key/value grids that read
  wide (3-up) and narrow (stacked). The full tier table + invariants are in
  `docs/ux-visual-rules.md` § **Responsive layout** — narrow is a first-class
  layout (below 900px the ledger becomes labeled cards), never an afterthought.

## Step 2 — Review dimensions

Go through each and note file:line + the concrete rule broken:

1. **Colour misuse** — `--accent` used for status? A "bad" state not red? A colour
   reused for two meanings? A status with colour but no distinguishing glyph?
2. **Icon consistency** — support/blocker/pulse/gate/tag/stage marks all follow the
   colour+glyph table? Same state → same colour everywhere?
3. **Neutrality** — engine order/weight; any vendor-favouring wording.
4. **Duplication** — any fact or link rendered twice; anything that should be a
   sub-level shown as a sibling section (or vice-versa).
5. **Hierarchy** — is it clear what is a blocker vs a detail? Blockers at one
   level, breakdowns nested.
6. **Responsive** — check against every tier in `docs/ux-visual-rules.md`
   § Responsive layout, not just "does it look narrow-friendly". Concretely: any
   bare `1fr`/fixed track around text that can overflow; `white-space: nowrap` on
   user-length text; a new first-level cell missing `data-label` (renders
   unlabeled as a card); a right-aligned value that goes ragged when stacked; a
   two-end header that doesn't `flex-wrap`.
7. **Noise** — low-signal rows that don't earn their place.

For a thorough pass, spawn one review agent per dimension in parallel (like
/simplify); for a quick pass, review inline.

## Step 3 — Report

List findings most-severe first: `file:line — rule broken — concrete fix`. If the
UI is already consistent, say so. Do **not** silently edit — report, then the
caller (or a follow-up) applies fixes and re-runs this skill.

## Step 4 — Keep the rules current

If a review establishes a *new* convention (a new status colour, a new icon), add
it to `docs/ux-visual-rules.md` so the rule and the UI stay in sync.
</content>
