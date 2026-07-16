"""Pure, vendor-neutral computations for the expandable per-spec view.

No I/O, no network — everything here is unit-testable from primitives and the
plain model types. Unknown inputs degrade gracefully (``unknown``/``None``)
rather than raising.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from mediawg_dashboard import links
from mediawg_dashboard.model import (
    Blocker,
    EngineRow,
    HorizontalReviews,
    InteropStatus,
    Pulse,
    Registry,
    RegistryStage,
    RegistryView,
    Spec,
    SpecMilestones,
    SpecView,
    Stage,
    SupportState,
)

PRE_CR_STAGES = {"ED", "FPWD", "WD"}

# --- Rec-track gate model (from docs/spec-process-flow.md) ---

# Current maturity stage -> the next meaningful transition (None if terminal).
NEXT_GATE: dict[str, str | None] = {
    "ED": "FPWD",
    "FPWD": "CR",
    "WD": "CR",
    "CR": "PR",
    "CR-snapshot": "PR",
    "CR-draft": "PR",
    "PR": "REC",
    "REC": None,
    "NOTE": None,
    "Discontinued": None,
    "unknown": None,
}


def next_gate(stage: Stage) -> str | None:
    """The next Rec-track transition for ``stage`` (None if terminal/unknown)."""
    return NEXT_GATE.get(stage)


# Ordinal for comparing how far along the Rec track a stage is.
STAGE_ORDER: dict[str, int] = {
    "ED": 0, "FPWD": 1, "WD": 2,
    "CR-snapshot": 3, "CR-draft": 3, "CR": 3,
    "PR": 4, "REC": 5,
    "NOTE": -1, "Discontinued": -1, "unknown": -1,
}

_QUARTER_END = {"Q1": (3, 31), "Q2": (6, 30), "Q3": (9, 30), "Q4": (12, 31)}


def parse_charter_target(target: str | None) -> tuple[str, date] | None:
    """Parse a charter target like 'CR Q4 2025' -> ('CR', date(2025, 12, 31)).

    Returns None if the string can't be parsed.
    """
    if not target:
        return None
    parts = target.split()
    if len(parts) != 3:
        return None
    stage, quarter, year = parts
    if quarter not in _QUARTER_END or not year.isdigit():
        return None
    month, day = _QUARTER_END[quarter]
    return (stage, date(int(year), month, day))


def charter_overdue(target: str | None, today: date, stage: Stage) -> bool:
    """True if the charter target quarter has passed and the spec hasn't reached it."""
    parsed = parse_charter_target(target)
    if parsed is None:
        return False
    target_stage, target_end = parsed
    behind = STAGE_ORDER.get(stage, -1) < STAGE_ORDER.get(target_stage, 99)
    return today > target_end and behind


def compute_stage_age_days(last_tr_publication: date | None, today: date) -> int | None:
    """Approximate days spent in the current stage (uses last /TR/ publication)."""
    if last_tr_publication is None:
        return None
    return (today - last_tr_publication).days


def trend_direction(series: list[int]) -> str:
    """Direction of a numeric series (oldest→newest): rising / falling / flat."""
    values = [v for v in series if v is not None]
    if len(values) < 2:
        return "flat"
    delta = values[-1] - values[0]
    return "rising" if delta > 0 else "falling" if delta < 0 else "flat"


def format_duration_days(days: int | None) -> str:
    """Human duration for the panel: '12d', '5mo', '2y 1m' ('—' if unknown)."""
    if days is None:
        return "—"
    if days < 60:
        return f"{days}d"
    if days < 365:
        return f"{days // 30}mo"
    years, rem_months = days // 365, (days % 365) // 30
    return f"{years}y {rem_months}m" if rem_months else f"{years}y"


_BLOCKER_GLYPHS = {"done": "✔", "open": "✘", "partial": "◐", "unknown": "·"}


def blocker_glyph(state: str) -> str:
    """Checklist mark for a blocker state (done/open/partial/unknown)."""
    return _BLOCKER_GLYPHS.get(state, "·")


_READINESS_GLYPHS = {"ready": "✓", "blocked": "✗", "unknown": "·"}


def readiness_glyph(readiness: str | None) -> str | None:
    """Colour+shape mark for next-gate readiness (None if terminal)."""
    return _READINESS_GLYPHS.get(readiness) if readiness else None


def _bool_state(value: bool | None) -> str:
    if value is None:
        return "unknown"
    return "done" if value else "open"


# Display name -> attribute for the 5 horizontal reviews (single source of order).
HORIZONTAL_FIELDS: tuple[tuple[str, str], ...] = (
    ("a11y", "a11y"),
    ("i18n", "i18n"),
    ("privacy", "privacy"),
    ("security", "security"),
    ("TAG", "tag"),
)


def horizontal_summary(h: HorizontalReviews) -> tuple[str, int, int]:
    """Aggregate the 5 horizontal reviews.

    Returns ``(state, resolved, total)`` where ``total`` excludes ``na`` reviews
    and ``state`` is one of done/partial/open/unknown.
    """
    considered = [s for s in (getattr(h, attr) for _, attr in HORIZONTAL_FIELDS) if s != "na"]
    total = len(considered)
    resolved = sum(1 for s in considered if s == "resolved")
    if total == 0:
        return ("done", 0, 0)
    if all(s == "unknown" for s in considered):
        return ("unknown", resolved, total)
    if resolved == total:
        return ("done", resolved, total)
    if resolved == 0:
        return ("open", resolved, total)
    return ("partial", resolved, total)


# --- Gate requirements: one declarative table, heterogeneous per gate ---
#
# Each requirement is a pure function of the spec's milestones returning a
# Blocker (label may be dynamic, e.g. "Horizontal reviews 3/5"). Adding a new
# gate or milestone is a table edit, not another if-branch.

Requirement = Callable[[SpecMilestones], Blocker]


def _wide_review_req(m: SpecMilestones) -> Blocker:
    return Blocker(label="Wide review complete", state=_bool_state(m.wide_review_complete), kind="wide_review")


def _horizontal_req(m: SpecMilestones) -> Blocker:
    state, resolved, total = horizontal_summary(m.horizontal)
    return Blocker(label=f"Horizontal reviews {resolved}/{total}", state=state, kind="horizontal")


def _cr_issues_req(m: SpecMilestones) -> Blocker:
    n = m.cr_blocking_issues_open
    state = "unknown" if n is None else ("done" if n == 0 else "open")
    label = f"CR-blocking issues ({n} open)" if n else "CR-blocking issues"
    return Blocker(label=label, state=state, kind="cr_blocking")


def _impl_report_req(m: SpecMilestones) -> Blocker:
    return Blocker(label="Implementation report", state=_bool_state(m.impl_report_ready), kind="impl_report")


def _ac_review_req(m: SpecMilestones) -> Blocker:
    return Blocker(label="AC review", state=_bool_state(m.ac_review_done), kind="ac_review")


GATE_REQUIREMENTS: dict[str, list[Requirement]] = {
    "FPWD": [],  # ED -> FPWD is a publication decision; no tracked process blockers.
    # Horizontal is last so its nested per-group chips sit at the bottom of the list.
    "CR": [_wide_review_req, _cr_issues_req, _horizontal_req],
    "PR": [_impl_report_req],
    "REC": [_ac_review_req],
}


def gate_requirements(gate: str | None) -> list[Requirement]:
    """The requirement checks that gate the given transition (empty if none)."""
    if gate is None:
        return []
    return GATE_REQUIREMENTS.get(gate, [])


def compute_blockers(stage: Stage, milestones: SpecMilestones) -> list[Blocker]:
    """The blocker checklist for the spec's *next* gate (empty if terminal)."""
    return [req(milestones) for req in gate_requirements(next_gate(stage))]


def _blocker_href(kind: str, meta) -> str | None:
    """Link each blocker to where its status actually lives (None if no venue).

    - horizontal → the cross-group horizontal-issue-tracker view for the spec
    - wide_review → the W3C Process definition (there's no single tracking venue;
      completion is a WG/chair judgment, set via config — see wide_review_complete)
    - cr_blocking → open ``*-needs-resolution`` issues (the must-resolve set)
    """
    if kind == "horizontal":
        return links.hr_review_url(meta.hr_shortname or meta.shortname)
    if kind == "wide_review":
        return links.wide_review_url()
    if kind == "cr_blocking":
        return links.needs_resolution_url(meta.repo)
    return None


def _readiness(gate: str | None, blockers: list[Blocker]) -> str | None:
    if gate is None:
        return None
    if not blockers:
        return "ready"
    states = {b.state for b in blockers}
    if states & {"open", "partial"}:
        return "blocked"
    if states == {"done"}:
        return "ready"
    return "unknown"


def gate_readiness(stage: Stage, milestones: SpecMilestones) -> str | None:
    """Readiness of the next gate: ready / blocked / unknown (None if terminal)."""
    return _readiness(next_gate(stage), compute_blockers(stage, milestones))


# --- Interop presentation (neutral: alphabetical Chrome/Firefox/Safari) ---

_GLYPHS: dict[str, str] = {
    "shipped": "●",
    "partial": "◐",
    "none": "○",
    "unknown": "·",
}


def support_glyph(state: SupportState) -> str:
    return _GLYPHS.get(state, _GLYPHS["unknown"])


def _engine_rows(interop: InteropStatus) -> list[EngineRow]:
    """Per-engine interop lines: MDN support + version + experimental WPT + MDN link."""
    anchor = f"{interop.mdn_url}#browser_compatibility" if interop.mdn_url else None
    data = (
        ("Chromium", interop.chrome, interop.chrome_version, interop.wpt_chrome),
        ("Firefox", interop.firefox, interop.firefox_version, interop.wpt_firefox),
        ("Safari", interop.safari, interop.safari_version, interop.wpt_safari),
    )
    return [
        EngineRow(
            name=name,
            state=state,
            glyph=support_glyph(state),
            version=version,
            wpt=f"{wpt[0]}/{wpt[1]}" if wpt else None,
            href=anchor,
        )
        for name, state, version, wpt in data
    ]


def shipping_cross_engine(specs: list[Spec]) -> int:
    """Count specs shipped in all three engines (the neutral interop headline)."""
    return sum(
        1
        for s in specs
        if s.interop.chrome == "shipped"
        and s.interop.firefox == "shipped"
        and s.interop.safari == "shipped"
    )


# --- Pulse (health/momentum), worst-tier wins ---

_STALE_AT_RISK_DAYS = 180
_STALE_WATCH_DAYS = 90
_BLOCKER_AT_RISK_DAYS = 90


def compute_pulse(
    days_since_activity: int | None,
    oldest_blocker_days: int | None,
    charter_overdue: bool = False,
    stage_before_cr: bool = False,
) -> Pulse:
    """Roll spec health into one tier + a short reason. None inputs skip a rule."""
    # at-risk (any)
    if days_since_activity is not None and days_since_activity >= _STALE_AT_RISK_DAYS:
        return Pulse(tier="at-risk", reason=f"no activity {days_since_activity}d")
    if oldest_blocker_days is not None and oldest_blocker_days >= _BLOCKER_AT_RISK_DAYS:
        return Pulse(tier="at-risk", reason=f"blocker open {oldest_blocker_days}d")
    if charter_overdue and stage_before_cr:
        return Pulse(tier="at-risk", reason="past charter target")

    # watch (any)
    if days_since_activity is not None and days_since_activity >= _STALE_WATCH_DAYS:
        return Pulse(tier="watch", reason=f"quiet {days_since_activity}d")

    return Pulse(tier="on-track", reason="active")


def spec_view(spec: Spec, today: date) -> SpecView:
    """Assemble the typed payload the first/second-level template renders per spec.

    Pure: derives everything from the spec's own fields. Pulse is None until any
    health input is present, so the UI shows '—' rather than a false 'on-track'.
    """
    stage = spec.status.stage
    gate = next_gate(stage)
    blockers = compute_blockers(stage, spec.milestones)
    readiness = _readiness(gate, blockers)
    stage_age_days = compute_stage_age_days(spec.status.last_tr_publication, today)
    h = spec.health
    has_health = any(
        (
            h.charter_overdue,
            h.days_since_activity is not None,
            h.oldest_blocking_issue_days is not None,
        )
    )
    pulse = compute_pulse(
        days_since_activity=h.days_since_activity,
        oldest_blocker_days=h.oldest_blocking_issue_days,
        charter_overdue=h.charter_overdue,
        stage_before_cr=stage in PRE_CR_STAGES,
    )
    interop = spec.interop
    repo = spec.meta.repo
    hz = spec.milestones.horizontal
    return SpecView(
        spec=spec,
        next_gate=gate,
        readiness=readiness,
        readiness_glyph=readiness_glyph(readiness),
        # All gate requirements (incl. horizontal review) are blockers; the
        # horizontal one carries the per-group chips as its sub-level (below).
        blocker_rows=[
            (blocker_glyph(b.state), b.label, _blocker_href(b.kind, spec.meta), b.state, b.kind)
            for b in blockers
        ],
        horizontal_rows=[
            (name, getattr(hz, attr), links.horizontal_group_url(repo, attr)) for name, attr in HORIZONTAL_FIELDS
        ],
        engine_rows=_engine_rows(interop),
        wpt_href=links.wpt_url(spec.meta.wpt_path),
        needs_resolution_href=links.needs_resolution_url(repo),
        stage_age_days=stage_age_days,
        stage_age_label=format_duration_days(stage_age_days),
        pulse=pulse if has_health else None,
    )


# --- Registry Track gate model (Process §6.5.2) ---
#
# Parallel to the Rec track but simpler: Registry Draft → Candidate Snapshot
# (gate = wide/horizontal review) → W3C Registry (gate = AC review). No
# implementation/interop/WPT gate — registries document values, not behaviour.

REGISTRY_NEXT_GATE: dict[str, str | None] = {
    "Registry Draft": "Candidate Snapshot",
    "Candidate Snapshot": "W3C Registry",
    "W3C Registry": None,
    "unknown": None,
}


def registry_next_gate(stage: RegistryStage) -> str | None:
    """The next registry-track transition for ``stage`` (None if terminal)."""
    return REGISTRY_NEXT_GATE.get(stage)


# The gate requirements reuse the same declarative Requirement functions the Rec
# track uses (horizontal last so its nested chips sit at the bottom).
REGISTRY_GATE_REQUIREMENTS: dict[str, list[Requirement]] = {
    "Candidate Snapshot": [_wide_review_req, _horizontal_req],
    "W3C Registry": [_ac_review_req],
}


def registry_gate_requirements(gate: str | None) -> list[Requirement]:
    """The requirement checks that gate the given registry transition."""
    if gate is None:
        return []
    return REGISTRY_GATE_REQUIREMENTS.get(gate, [])


def compute_registry_blockers(stage: RegistryStage, milestones: SpecMilestones) -> list[Blocker]:
    """The blocker checklist for the registry's *next* gate (empty if terminal)."""
    return [req(milestones) for req in registry_gate_requirements(registry_next_gate(stage))]


def registry_gate_readiness(stage: RegistryStage, milestones: SpecMilestones) -> str | None:
    """Readiness of the registry's next gate: ready / blocked / unknown."""
    return _readiness(registry_next_gate(stage), compute_registry_blockers(stage, milestones))


def registry_view(registry: Registry, today: date) -> RegistryView:
    """Assemble the typed payload the template renders per registry (pure).

    Mirrors ``spec_view`` for the shared Stage/Next-gate/horizontal shape but
    over the registry track, and carries the entry count instead of interop.
    """
    stage = registry.status.stage
    gate = registry_next_gate(stage)
    blockers = compute_registry_blockers(stage, registry.milestones)
    readiness = _readiness(gate, blockers)
    hz = registry.milestones.horizontal
    review_state, resolved, total = horizontal_summary(hz)
    stage_age_days = compute_stage_age_days(registry.status.last_published, today)
    repo = registry.meta.repo
    return RegistryView(
        registry=registry,
        next_gate=gate,
        readiness=readiness,
        readiness_glyph=readiness_glyph(readiness),
        review_label=f"{resolved}/{total}",
        review_state=review_state,
        review_glyph=blocker_glyph(review_state),
        blocker_rows=[
            (blocker_glyph(b.state), b.label, _blocker_href(b.kind, registry.meta), b.state, b.kind)
            for b in blockers
        ],
        horizontal_rows=[
            (name, getattr(hz, attr), links.horizontal_group_url(repo, attr)) for name, attr in HORIZONTAL_FIELDS
        ],
        stage_age_days=stage_age_days,
        stage_age_label=format_duration_days(stage_age_days),
    )
