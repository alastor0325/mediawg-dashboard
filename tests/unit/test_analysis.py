from datetime import date

from mediawg_dashboard.analysis import (
    compute_blockers,
    compute_pulse,
    compute_stage_age_days,
    gate_requirements,
    horizontal_summary,
    interop_label,
    next_gate,
    support_glyph,
)
from mediawg_dashboard.model import (
    HorizontalReviews,
    InteropStatus,
    SpecMilestones,
)

# ---------------- next_gate ----------------


def test_next_gate_wd_is_cr():
    assert next_gate("WD") == "CR"


def test_next_gate_fpwd_is_cr():
    assert next_gate("FPWD") == "CR"


def test_next_gate_ed_is_fpwd():
    assert next_gate("ED") == "FPWD"


def test_next_gate_cr_variants_are_pr():
    assert next_gate("CR") == "PR"
    assert next_gate("CR-snapshot") == "PR"
    assert next_gate("CR-draft") == "PR"


def test_next_gate_pr_is_rec():
    assert next_gate("PR") == "REC"


def test_next_gate_terminal_stages_are_none():
    assert next_gate("REC") is None
    assert next_gate("NOTE") is None
    assert next_gate("Discontinued") is None
    assert next_gate("unknown") is None


# ---------------- stage age ----------------


def test_stage_age_none_when_no_publication():
    assert compute_stage_age_days(None, date(2026, 7, 13)) is None


def test_stage_age_counts_days():
    assert compute_stage_age_days(date(2026, 1, 1), date(2026, 7, 13)) == 193


# ---------------- horizontal_summary ----------------


def test_horizontal_summary_all_resolved_is_done():
    h = HorizontalReviews(
        a11y="resolved", i18n="resolved", privacy="resolved",
        security="resolved", tag="resolved",
    )
    assert horizontal_summary(h) == ("done", 5, 5)


def test_horizontal_summary_na_excluded_from_total():
    h = HorizontalReviews(
        a11y="resolved", i18n="na", privacy="resolved",
        security="resolved", tag="resolved",
    )
    assert horizontal_summary(h) == ("done", 4, 4)


def test_horizontal_summary_mixed_is_partial():
    h = HorizontalReviews(
        a11y="resolved", i18n="open", privacy="resolved",
        security="unknown", tag="resolved",
    )
    state, resolved, total = horizontal_summary(h)
    assert state == "partial"
    assert resolved == 3
    assert total == 5


def test_horizontal_summary_all_unknown_is_unknown():
    assert horizontal_summary(HorizontalReviews())[0] == "unknown"


def test_horizontal_summary_none_resolved_is_open():
    h = HorizontalReviews(
        a11y="open", i18n="open", privacy="requested",
        security="open", tag="open",
    )
    assert horizontal_summary(h)[0] == "open"


# ---------------- compute_blockers ----------------


def test_blockers_for_cr_gate_lists_wide_review_and_horizontal():
    m = SpecMilestones(
        wide_review_complete=False,
        horizontal=HorizontalReviews(
            security="resolved", privacy="resolved", tag="resolved",
            a11y="open", i18n="open",
        ),
        cr_blocking_issues_open=2,
    )
    blockers = compute_blockers("WD", m)
    labels = [b.label for b in blockers]
    assert any("Wide review" in x for x in labels)
    assert any("Horizontal reviews" in x for x in labels)
    # wide review not complete -> open
    wr = next(b for b in blockers if "Wide review" in b.label)
    assert wr.state == "open"
    # 3/5 resolved -> partial
    hr = next(b for b in blockers if "Horizontal reviews" in b.label)
    assert hr.state == "partial"
    assert "3/5" in hr.label


def test_blockers_cr_blocking_issues_done_when_zero():
    m = SpecMilestones(cr_blocking_issues_open=0)
    blockers = compute_blockers("WD", m)
    ci = next(b for b in blockers if "CR-blocking" in b.label)
    assert ci.state == "done"


def test_blockers_cr_blocking_issues_unknown_when_none():
    m = SpecMilestones(cr_blocking_issues_open=None)
    blockers = compute_blockers("WD", m)
    ci = next(b for b in blockers if "CR-blocking" in b.label)
    assert ci.state == "unknown"


def test_blockers_for_pr_gate_is_impl_report():
    m = SpecMilestones(impl_report_ready=False)
    blockers = compute_blockers("CR", m)
    labels = [b.label for b in blockers]
    assert any("Implementation report" in x for x in labels)


def test_blockers_terminal_stage_is_empty():
    assert compute_blockers("REC", SpecMilestones()) == []


def test_gate_requirements_table_driven():
    assert gate_requirements(None) == []
    assert gate_requirements("FPWD") == []
    assert len(gate_requirements("CR")) == 3
    assert len(gate_requirements("PR")) == 1
    assert len(gate_requirements("REC")) == 1


# ---------------- interop glyphs ----------------


def test_support_glyph_mapping():
    assert support_glyph("shipped") == "●"
    assert support_glyph("partial") == "◐"
    assert support_glyph("none") == "○"
    assert support_glyph("unknown") == "·"


def test_interop_label_alphabetical_cfs():
    i = InteropStatus(chrome="shipped", firefox="shipped", safari="partial")
    assert interop_label(i) == "C● F● S◐"


# ---------------- pulse ----------------


def test_pulse_at_risk_when_stale_180d():
    p = compute_pulse(days_since_activity=200, oldest_blocker_days=None)
    assert p.tier == "at-risk"
    assert "200" in p.reason


def test_pulse_at_risk_when_blocker_over_90d():
    p = compute_pulse(days_since_activity=10, oldest_blocker_days=140)
    assert p.tier == "at-risk"


def test_pulse_at_risk_when_charter_overdue_before_cr():
    p = compute_pulse(
        days_since_activity=10, oldest_blocker_days=None,
        charter_overdue=True, stage_before_cr=True,
    )
    assert p.tier == "at-risk"


def test_pulse_charter_overdue_after_cr_is_not_at_risk():
    p = compute_pulse(
        days_since_activity=10, oldest_blocker_days=None,
        charter_overdue=True, stage_before_cr=False,
    )
    assert p.tier != "at-risk"


def test_pulse_watch_when_quiet_90d():
    p = compute_pulse(days_since_activity=100, oldest_blocker_days=None)
    assert p.tier == "watch"


def test_pulse_watch_when_single_editor():
    p = compute_pulse(days_since_activity=5, oldest_blocker_days=None, single_editor=True)
    assert p.tier == "watch"


def test_pulse_on_track_default():
    p = compute_pulse(days_since_activity=5, oldest_blocker_days=10)
    assert p.tier == "on-track"


def test_pulse_handles_all_none_inputs():
    p = compute_pulse(days_since_activity=None, oldest_blocker_days=None)
    assert p.tier in {"on-track", "watch", "at-risk"}
