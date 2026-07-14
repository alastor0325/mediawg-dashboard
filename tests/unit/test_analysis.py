from datetime import date

from mediawg_dashboard.analysis import (
    blocker_glyph,
    charter_overdue,
    compute_blockers,
    compute_pulse,
    compute_stage_age_days,
    format_duration_days,
    gate_readiness,
    gate_requirements,
    horizontal_summary,
    interop_label,
    next_gate,
    parse_charter_target,
    spec_view,
    support_glyph,
)
from mediawg_dashboard.model import (
    HorizontalReviews,
    InteropStatus,
    RepoStats,
    Spec,
    SpecHealth,
    SpecMeta,
    SpecMilestones,
    SpecStatus,
)


def _spec(
    stage="WD",
    milestones=None,
    interop=None,
    health=None,
    last_tr=date(2026, 1, 1),
) -> Spec:
    return Spec(
        meta=SpecMeta(shortname="x", title="X", repo="w3c/x", w3c_shortname="x", wpt_path="/x/"),
        status=SpecStatus(stage=stage, last_tr_publication=last_tr),
        stats=RepoStats(open_issues_count=1, open_prs_count=0),
        milestones=milestones or SpecMilestones(),
        interop=interop or InteropStatus(),
        health=health or SpecHealth(),
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


# ---------------- duration + blocker glyph ----------------


def test_trend_direction():
    from mediawg_dashboard.analysis import trend_direction

    assert trend_direction([]) == "flat"
    assert trend_direction([5]) == "flat"
    assert trend_direction([5, 8]) == "rising"
    assert trend_direction([8, 5]) == "falling"
    assert trend_direction([5, 5]) == "flat"


def test_format_duration_days_none():
    assert format_duration_days(None) == "—"


def test_format_duration_days_buckets():
    assert format_duration_days(12) == "12d"
    assert format_duration_days(150) == "5mo"
    assert format_duration_days(400) == "1y 1m"
    assert format_duration_days(365) == "1y"


def test_blocker_glyph_mapping():
    assert blocker_glyph("done") == "✔"
    assert blocker_glyph("open") == "✘"
    assert blocker_glyph("partial") == "◐"
    assert blocker_glyph("unknown") == "·"


# ---------------- charter targets ----------------


def test_parse_charter_target_valid():
    assert parse_charter_target("CR Q4 2025") == ("CR", date(2025, 12, 31))
    assert parse_charter_target("REC Q2 2027") == ("REC", date(2027, 6, 30))


def test_parse_charter_target_invalid():
    assert parse_charter_target(None) is None
    assert parse_charter_target("soon") is None
    assert parse_charter_target("CR Q9 2025") is None


def test_charter_overdue_true_when_past_and_behind():
    # CR target end of 2025, still at WD in mid-2026 -> overdue.
    assert charter_overdue("CR Q4 2025", date(2026, 7, 13), "WD") is True


def test_charter_not_overdue_when_reached_stage():
    # Already at PR (past CR) -> not overdue even if the CR date passed.
    assert charter_overdue("CR Q4 2025", date(2026, 7, 13), "PR") is False


def test_charter_not_overdue_before_target_date():
    assert charter_overdue("CR Q4 2026", date(2026, 7, 13), "WD") is False


def test_charter_overdue_unparseable_is_false():
    assert charter_overdue(None, date(2026, 7, 13), "WD") is False


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


# ---------------- gate_readiness ----------------


def test_gate_readiness_terminal_is_none():
    assert gate_readiness("REC", SpecMilestones()) is None


def test_gate_readiness_ready_when_no_blockers():
    # ED -> FPWD has no tracked blockers.
    assert gate_readiness("ED", SpecMilestones()) == "ready"


def test_gate_readiness_blocked_when_any_open():
    m = SpecMilestones(wide_review_complete=False, cr_blocking_issues_open=3)
    assert gate_readiness("WD", m) == "blocked"


def test_gate_readiness_ready_when_all_done():
    m = SpecMilestones(
        wide_review_complete=True,
        horizontal=HorizontalReviews(
            a11y="resolved", i18n="resolved", privacy="resolved",
            security="resolved", tag="resolved",
        ),
        cr_blocking_issues_open=0,
    )
    assert gate_readiness("WD", m) == "ready"


def test_gate_readiness_unknown_when_all_unknown():
    assert gate_readiness("WD", SpecMilestones()) == "unknown"


# ---------------- spec_view ----------------


def test_spec_view_has_core_fields():
    v = spec_view(_spec(stage="WD"), date(2026, 7, 13))
    assert v.spec.status.stage == "WD"
    assert v.next_gate == "CR"
    assert v.interop_label == "C· F· S·"
    assert v.stage_age_days == 193


def test_spec_view_pulse_none_without_health_data():
    v = spec_view(_spec(), date(2026, 7, 13))
    assert v.pulse is None


def test_spec_view_pulse_present_with_health_data():
    v = spec_view(_spec(health=SpecHealth(days_since_activity=200)), date(2026, 7, 13))
    assert v.pulse is not None
    assert v.pulse.tier == "at-risk"


def test_spec_view_interop_label_reflects_support():
    v = spec_view(
        _spec(interop=InteropStatus(chrome="shipped", firefox="shipped", safari="partial")),
        date(2026, 7, 13),
    )
    assert v.interop_label == "C● F● S◐"


def test_spec_view_engine_rows_alphabetical_with_glyph_and_link():
    v = spec_view(
        _spec(interop=InteropStatus(chrome="shipped", firefox="none", safari="partial")),
        date(2026, 7, 13),
    )
    assert [name for name, *_ in v.engine_rows] == ["Chrome", "Firefox", "Safari"]
    # (name, state, glyph, href) — href is None without a webstatus_id.
    assert v.engine_rows[0] == ("Chrome", "shipped", "●", None)


def test_spec_view_horizontal_rows_ordered_and_linked():
    v = spec_view(_spec(), date(2026, 7, 13))
    assert [name for name, *_ in v.horizontal_rows] == ["a11y", "i18n", "privacy", "security", "TAG"]
    # Each horizontal chip links to its group's GitHub issue filter.
    _, _, href = v.horizontal_rows[0]
    assert "w3c/x/issues" in href and "a11y-needs-resolution" in href


def test_spec_view_blocker_rows_link_github_derived_only():
    v = spec_view(_spec(stage="WD"), date(2026, 7, 13))
    by_label = {label: href for _, label, href in v.blocker_rows}
    # Wide review is config-derived -> no link.
    assert by_label["Wide review complete"] is None
    # CR-blocking issues comes from labels -> links to the needs-resolution filter.
    cr = next(h for lbl, h in by_label.items() if lbl.startswith("CR-blocking"))
    assert cr is not None and "needs-resolution" in cr
