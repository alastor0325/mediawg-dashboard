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
| `--signal-blue` | blue | neutral Rec-track stage marker | CR stage pip only |
| `--accent` | rust | **interactive only** — links, hover, brand | never a status colour |

**Rule:** `--accent` is for interactivity (links/hover/wordmark), never to encode
status. "Bad" is always `--signal-rose`, not accent.

## Icons: colour + shape (never colour alone)

Every status is encoded by **both** a colour and a distinct glyph, so it survives
colour-blindness and greyscale.

| State | Support | Blocker checklist | Meaning |
|---|---|---|---|
| good | `●` green | `✔` green | shipped / done |
| caution | `◐` amber | `◐` amber | partial |
| bad | `○` red | `✘` red | none / open |
| unknown | `·` grey | `·` grey | no data |

- **Support tri-dot** (first level + panel): three engines, always **alphabetical
  Chromium / Firefox / Safari**, equal weight, each a coloured glyph + the engine
  initial (C/F/S). Read the column vertically = the WG's interop landscape.
- **Pulse / gate readiness**: a solid coloured dot (`.hdot`) + a trailing text tag
  in the same colour family.
- Tags (`ready` / `blocked` / `behind charter` / pulse tiers) are coloured text
  per the table above.

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
- Panel = three groups, each an aligned key/value grid (`dl.panel-kv`,
  `max-content 1fr`) so labels/values line up wide (3-up) and narrow (stacked).
- Show a signal only when it's meaningful (e.g. backlog trend needs ≥2 snapshots;
  "behind charter" only when overdue).

## Typography

- Labels / codes / numbers: `IBM Plex Mono`. Spec titles: `Fraunces`. Body:
  `Plus Jakarta Sans`. Tabular numerals for counts.
</content>
