# mediawg-dashboard — visual rules

The dashboard's look is an "editorial ledger": restrained, monospace-accented,
one system. These rules keep status signals consistent and accessible. Enforced
by the `mediawg-dashboard-ux-review` skill.

## Colour semantics (one meaning per colour)

| Token | Colour | Means | Used for |
|---|---|---|---|
| `--signal-green` | green | good / done / shipped / ready / on-track / resolved | support shipped, blocker done, gate ready, pulse on-track, horizontal resolved |
| `--signal-amber` | amber | caution / partial / in-progress / requested / watch | support partial, blocker partial, pulse watch, horizontal requested |
| `--signal-rose` | red | bad / none / open / blocked / at-risk / overdue | support none, blocker open, gate blocked, pulse at-risk, "behind charter", horizontal open |
| `--signal-mute` | grey | unknown / no data / N/A | any "unknown" state |
| `--signal-blue` | blue | neutral intermediate-stage marker | CR stage pip + Candidate-Snapshot registry pip |
| `--accent` | rust | **interactive only** — links, hover, brand | never a status colour |

**Rule:** `--accent` is for interactivity (links/hover/wordmark), never to encode
status. "Bad" is always `--signal-rose`, not accent.

## Icons: colour + shape (never colour alone)

Every status is encoded by **both** a colour and a distinct glyph, so it survives
colour-blindness and greyscale.

| State | Support | Blocker / review chip | Meaning |
|---|---|---|---|
| good | `●` green | `✔` green | shipped / done / resolved |
| caution | `◐` amber | `◐` amber | partial / requested / in-progress |
| bad | `○` red | `✘` red | none / open |
| n/a | — | `–` grey (dashed) | not applicable |
| unknown | `·` grey | `·` grey (dashed) | no data |

- **Support tri-dot** (first level + panel): three engines, always **alphabetical
  Chromium / Firefox / Safari**, equal weight, each a coloured glyph + the engine
  initial (C/F/S). Read the column vertically = the WG's interop landscape.
- **Pulse**: a solid coloured dot (`.hdot`, colour = tier) + the reason text
  (which differs per tier, e.g. "no activity 327d"). No tier word — the dot
  colour + reason already carry severity + cause.
- **Gate readiness**: a colour+glyph mark (✓/✗/·) at first level; a coloured
  text tag (ready/blocked) in the panel.
- Tags (`ready` / `blocked` / `behind charter` / pulse tiers) are coloured text
  per the table above.

## Registries section (registry track)

- A second ledger below the specs table; shares the stage/next-gate/horizontal
  model but has **no interop/WPT/pulse axis** (a registry documents values, it
  isn't shipped or tested) — so those columns are simply absent, with no
  explanatory note needed.
- **Column alignment:** both ledgers emit the **same `<colgroup>`** (identical
  `col-*` widths) so their columns line up across sections — Stage under Stage,
  Next under Next. Don't give the registries table its own column widths.
- **No overflow:** panel content must never spill outside its box. Registered
  values must be allowed to wrap (`overflow-wrap`, never `white-space: nowrap`
  on a value that can be long); grid/column tracks use `minmax(min(…,100%),1fr)`
  so a narrow container can't force horizontal scroll.
- **Stage pip** (`.rstage`): amber = Registry Draft (in progress), blue =
  Candidate Snapshot (intermediate, mirrors CR), green = W3C Registry (final);
  colour + the full stage name as text (same pattern as spec `.stage`).
- **Registered entries** are **data, not status** — plain value (mono ink) +
  note (muted), no glyph/colour. The layout adapts so nothing wastes space:
  grouped entries render **one column per group** side by side (e.g.
  Audio | Video); bare values with no notes (e.g. HDCP versions) render as a
  **compact inline token row**; value+note lists flow into columns with the note
  **stacked under the value on every row** (consistent — a note never stays
  inline just because it happens to fit). The first-level Review and Entries
  columns are **centre-aligned** (header + value) so their short content is
  balanced within the wide shared columns, rather than hugging one edge. Use block
  markup (not a nested `<table>`, whose cells inherit the ledger's row styling).
- The registry's `/TR/` is linked **once** (the title); don't repeat it on the
  publication date or the entries header.

## Neutrality

Engines are always listed alphabetically with identical weight/size; no vendor
logos, no "reference browser", no "outlier/laggard" language. (See the
`dashboard-must-be-neutral` memory.)

## Layout / dedup

- Each fact and each link appears **once**. (repo ← spec path; ED ← title; /TR/ ←
  publication date; wpt.fyi ← WPT section; issues/PRs ← their own rows.)
- **Horizontal review is a CR blocker** — render it as one line *inside* the
  "Blockers to <gate>" checklist (with its aggregate state mark), and nest the 5
  per-group chips directly beneath it as a sub-level. Never a separate top-level
  "Horizontal reviews" section (that made it ambiguous whether it's a blocker).
  Items at the same hierarchy level = same section; breakdowns = sub-level.
  Each per-group chip carries **colour + glyph + the state word** (all three, so
  the state is obvious), laid out in an even grid, and **links to the actual
  review issue** — not to an empty label search on the spec's own repo.
  State semantics: **resolved** = review request closed *and* no open
  `<group>-needs-resolution`; **open** = an open `<group>-needs-resolution` on
  the spec repo (a review-raised blocker — this wins even if the request is
  closed, because "review complete" ≠ "concerns resolved"), linked to that issue;
  **requested** = review request still open; **unknown** = no matching issue.
- Panel = three groups, each an aligned key/value grid (`dl.panel-kv`,
  `max-content 1fr`) so labels/values line up wide (3-up) and narrow (stacked).
- Show a signal only when it's meaningful (e.g. backlog trend needs ≥2 snapshots;
  "behind charter" only when overdue).
- **Blocker order:** simple booleans first, then the one with a nested breakdown
  (horizontal review) last, so its sub-chips sit at the bottom.

## Affordance & interaction

- **Expandable rows must look expandable:** a disclosure caret (`▸`) visible at
  rest (muted), brightening to accent on hover/focus and rotating when open;
  `cursor: pointer`; and a one-line hint in the section subtitle. Rows are
  keyboard-operable: `tabindex=0`, visible focus ring, Enter/Space toggles, and
  `aria-expanded` reflects state.

## Typography

- Labels / codes / numbers: `IBM Plex Mono`. Spec titles: `Fraunces`. Body:
  `Plus Jakarta Sans`. Tabular numerals for counts.
</content>
