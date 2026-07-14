"""Pure, vendor-neutral computations for the expandable per-spec view.

No I/O, no network — everything here is unit-testable from primitives and the
plain model types. Unknown inputs degrade gracefully (``unknown``/``None``)
rather than raising.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from mediawg_dashboard.model import (
    Blocker,
    HorizontalReviews,
    InteropStatus,
    Pulse,
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


def compute_stage_age_days(last_tr_publication: date | None, today: date) -> int | None:
    """Approximate days spent in the current stage (uses last /TR/ publication)."""
    if last_tr_publication is None:
        return None
    return (today - last_tr_publication).days


def _bool_state(value: bool | None) -> str:
    if value is None:
        return "unknown"
    return "done" if value else "open"


def horizontal_summary(h: HorizontalReviews) -> tuple[str, int, int]:
    """Aggregate the 5 horizontal reviews.

    Returns ``(state, resolved, total)`` where ``total`` excludes ``na`` reviews
    and ``state`` is one of done/partial/open/unknown.
    """
    considered = [s for s in (h.a11y, h.i18n, h.privacy, h.security, h.tag) if s != "na"]
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
    return Blocker(label="Wide review complete", state=_bool_state(m.wide_review_complete))


def _horizontal_req(m: SpecMilestones) -> Blocker:
    state, resolved, total = horizontal_summary(m.horizontal)
    return Blocker(label=f"Horizontal reviews {resolved}/{total}", state=state)


def _cr_issues_req(m: SpecMilestones) -> Blocker:
    n = m.cr_blocking_issues_open
    state = "unknown" if n is None else ("done" if n == 0 else "open")
    label = f"CR-blocking issues ({n} open)" if n else "CR-blocking issues"
    return Blocker(label=label, state=state)


def _impl_report_req(m: SpecMilestones) -> Blocker:
    return Blocker(label="Implementation report", state=_bool_state(m.impl_report_ready))


def _ac_review_req(m: SpecMilestones) -> Blocker:
    return Blocker(label="AC review", state=_bool_state(m.ac_review_done))


GATE_REQUIREMENTS: dict[str, list[Requirement]] = {
    "FPWD": [],  # ED -> FPWD is a publication decision; no tracked process blockers.
    "CR": [_wide_review_req, _horizontal_req, _cr_issues_req],
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


def interop_label(interop: InteropStatus) -> str:
    """Compact tri-engine label, e.g. ``C● F● S◐`` (alphabetical, even weight)."""
    return (
        f"C{support_glyph(interop.chrome)} "
        f"F{support_glyph(interop.firefox)} "
        f"S{support_glyph(interop.safari)}"
    )


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
    single_editor: bool = False,
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
    if single_editor:
        return Pulse(tier="watch", reason="single editor")

    return Pulse(tier="on-track", reason="active")


def spec_view(spec: Spec, today: date) -> SpecView:
    """Assemble the typed payload the first/second-level template renders per spec.

    Pure: derives everything from the spec's own fields. Pulse is None until any
    health input is present, so the UI shows '—' rather than a false 'on-track'.
    """
    stage = spec.status.stage
    gate = next_gate(stage)
    blockers = compute_blockers(stage, spec.milestones)
    h = spec.health
    has_health = any(
        (
            h.charter_overdue,
            h.days_since_activity is not None,
            h.oldest_blocking_issue_days is not None,
            h.editor_count is not None,
        )
    )
    pulse = compute_pulse(
        days_since_activity=h.days_since_activity,
        oldest_blocker_days=h.oldest_blocking_issue_days,
        charter_overdue=h.charter_overdue,
        stage_before_cr=stage in PRE_CR_STAGES,
        single_editor=h.editor_count == 1,
    )
    return SpecView(
        spec=spec,
        next_gate=gate,
        readiness=_readiness(gate, blockers),
        blockers=blockers,
        interop_label=interop_label(spec.interop),
        wpt_pct=spec.interop.all_engines_wpt,
        stage_age_days=compute_stage_age_days(spec.status.last_tr_publication, today),
        pulse=pulse if has_health else None,
    )
