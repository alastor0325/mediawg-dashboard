from datetime import date, datetime, timedelta, timezone

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
    next_gate,
    parse_charter_target,
    readiness_glyph,
    spec_view,
    support_glyph,
)
from mediawg_dashboard.model import (
    ActivityEvent,
    HorizontalReviews,
    InteropStatus,
    RepoStats,
    Spec,
    SpecActivity,
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
    activity=None,
) -> Spec:
    return Spec(
        meta=SpecMeta(shortname="x", title="X", repo="w3c/x", w3c_shortname="x", wpt_path="/x/"),
        status=SpecStatus(stage=stage, last_tr_publication=last_tr),
        stats=RepoStats(open_issues_count=1, open_prs_count=0),
        milestones=milestones or SpecMilestones(),
        interop=interop or InteropStatus(),
        health=health or SpecHealth(),
        activity=activity or SpecActivity(),
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


def test_blockers_for_cr_gate_lists_concrete_items_only():
    m = SpecMilestones(
        horizontal=HorizontalReviews(
            security="resolved", privacy="resolved", tag="resolved",
            a11y="open", i18n="open",
        ),
        cr_blocking_issues_open=2,
    )
    blockers = compute_blockers("WD", m)
    kinds = [b.kind for b in blockers]
    # Only concrete, trackable blockers — no broad "wide review" item.
    assert kinds == ["cr_blocking", "horizontal"]
    assert not any("Wide review" in b.label for b in blockers)
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
    assert len(gate_requirements("CR")) == 2  # cr_blocking + horizontal (no wide review)
    assert len(gate_requirements("PR")) == 1
    assert len(gate_requirements("REC")) == 1


# ---------------- interop glyphs ----------------


def test_support_glyph_mapping():
    assert support_glyph("shipped") == "●"
    assert support_glyph("partial") == "◐"
    assert support_glyph("none") == "○"
    assert support_glyph("unknown") == "·"


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


def test_readiness_glyph_mapping():
    assert readiness_glyph("ready") == "✓"
    assert readiness_glyph("blocked") == "✗"
    assert readiness_glyph("unknown") == "·"
    assert readiness_glyph(None) is None  # terminal gate -> no mark


def test_spec_view_sets_readiness_glyph():
    v = spec_view(_spec(stage="WD"), date(2026, 7, 13))
    assert v.readiness in {"ready", "blocked", "unknown"}
    assert v.readiness_glyph in {"✓", "✗", "·"}


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
    m = SpecMilestones(cr_blocking_issues_open=3)
    assert gate_readiness("WD", m) == "blocked"


def test_gate_readiness_ready_when_all_done():
    m = SpecMilestones(
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
    assert [e.name for e in v.engine_rows] == ["Chromium", "Firefox", "Safari"]
    assert v.stage_age_days == 193


def test_spec_view_pulse_none_without_health_data():
    v = spec_view(_spec(), date(2026, 7, 13))
    assert v.pulse is None


def test_spec_view_pulse_present_with_health_data():
    v = spec_view(_spec(health=SpecHealth(days_since_commit=200)), date(2026, 7, 13))
    assert v.pulse is not None
    assert v.pulse.tier == "at-risk"


def test_spec_view_engine_rows_alphabetical_with_glyph_version_wpt():
    v = spec_view(
        _spec(interop=InteropStatus(
            chrome="shipped", firefox="none", safari="partial",
            chrome_version="94", wpt_chrome=(38, 40),
            mdn_url="https://developer.mozilla.org/docs/Web/API/X",
        )),
        date(2026, 7, 13),
    )
    assert [e.name for e in v.engine_rows] == ["Chromium", "Firefox", "Safari"]
    chromium = v.engine_rows[0]
    assert chromium.state == "shipped" and chromium.glyph == "●"
    assert chromium.version == "94"
    assert chromium.wpt == "38/40"
    assert chromium.href.endswith("#browser_compatibility")


def test_spec_view_engine_rows_no_mdn_url_has_no_link():
    v = spec_view(_spec(), date(2026, 7, 13))
    assert all(e.href is None for e in v.engine_rows)


def test_spec_view_horizontal_rows_ordered_and_linked():
    v = spec_view(_spec(), date(2026, 7, 13))
    assert [name for name, *_ in v.horizontal_rows] == ["a11y", "i18n", "privacy", "security", "TAG"]
    # With no known issue URL, the chip falls back to the group's request repo.
    _, _, href = v.horizontal_rows[0]
    assert "w3c/a11y-request/issues" in href


def test_spec_view_horizontal_chip_deep_links_to_actual_issue():
    spec = _spec(
        milestones=SpecMilestones(
            horizontal_urls={"a11y": "https://github.com/w3c/a11y-request/issues/39"}
        )
    )
    v = spec_view(spec, date(2026, 7, 13))
    a11y_href = v.horizontal_rows[0][2]
    assert a11y_href == "https://github.com/w3c/a11y-request/issues/39"


def test_spec_view_blocker_rows_include_horizontal_and_link_venues():
    v = spec_view(_spec(stage="WD"), date(2026, 7, 13))
    by_label = {label: href for _, label, href, _, _ in v.blocker_rows}
    kinds = {kind for *_, kind in v.blocker_rows}
    # Horizontal review IS a CR blocker (nested chips render under it).
    assert "horizontal" in kinds
    # No broad "wide review" blocker — only concrete items.
    assert "Wide review complete" not in by_label
    assert "wide_review" not in kinds
    # Horizontal reviews -> the cross-group horizontal-issue-tracker view.
    hz = next(h for lbl, h in by_label.items() if lbl.startswith("Horizontal reviews"))
    assert "review.html?shortname=" in hz
    # CR-blocking issues -> the open needs-resolution filter.
    cr = next(h for lbl, h in by_label.items() if lbl.startswith("CR-blocking"))
    assert cr is not None and "needs-resolution" in cr


# ---------------- spec_view: activity digest ----------------


def _activity_event(number=1, event="comment", days_ago=1, author="alice"):
    return ActivityEvent(
        number=number,
        kind="issue",
        title=f"thread {number}",
        url=f"https://github.com/w3c/x/issues/{number}",
        state="open",
        event=event,
        author=author,
        at=datetime(2026, 7, 13, 12, 0, tzinfo=timezone.utc) - timedelta(days=days_ago),
    )


def test_spec_view_activity_none_when_unknown():
    """A failed activity fetch must render '—' and suppress the badge."""
    v = spec_view(_spec(activity=SpecActivity(known=False)), date(2026, 7, 13))
    assert v.activity is None


def test_spec_view_activity_zero_when_known_and_empty():
    v = spec_view(_spec(activity=SpecActivity(known=True)), date(2026, 7, 13))
    assert v.activity is not None
    assert v.activity.event_count == 0
    assert v.activity.threads == []


def test_spec_view_activity_counts_events_and_threads():
    activity = SpecActivity(
        known=True,
        events=[
            _activity_event(number=1, event="opened", days_ago=3),
            _activity_event(number=1, days_ago=2),
            _activity_event(number=2, days_ago=1),
        ],
    )
    v = spec_view(_spec(activity=activity), date(2026, 7, 13))
    assert v.activity.event_count == 3
    assert v.activity.thread_count == 2
    assert [t.number for t in v.activity.threads] == [2, 1]
    assert v.activity.since == date(2026, 7, 6)


def test_spec_view_activity_drops_stale_events_outside_the_window():
    activity = SpecActivity(known=True, events=[_activity_event(days_ago=40)])
    v = spec_view(_spec(activity=activity), date(2026, 7, 13))
    assert v.activity.event_count == 0


# ---------------- Pulse must not contradict the activity badge ----------------


def test_spec_view_pulse_counts_discussion_not_just_commits():
    """The reported bug: 272 days without a commit but comments this week showed
    "no activity 272d" right beside a "2 new" badge."""
    v = spec_view(
        _spec(
            health=SpecHealth(days_since_commit=272),
            activity=SpecActivity(known=True, last_discussion_days=1, events=[_activity_event()]),
        ),
        date(2026, 7, 13),
    )
    assert v.pulse.tier == "on-track"
    assert "no activity" not in v.pulse.reason


def test_spec_view_pulse_still_stale_when_both_sources_are_quiet():
    v = spec_view(
        _spec(
            health=SpecHealth(days_since_commit=272),
            activity=SpecActivity(known=True, last_discussion_days=300),
        ),
        date(2026, 7, 13),
    )
    assert v.pulse.tier == "at-risk"
    assert "no activity 272d" in v.pulse.reason  # the more recent of the two


def test_spec_view_pulse_uses_commits_when_discussion_unknown():
    v = spec_view(_spec(health=SpecHealth(days_since_commit=200)), date(2026, 7, 13))
    assert v.pulse.tier == "at-risk"


def test_spec_view_pulse_uses_discussion_when_commits_unknown():
    v = spec_view(
        _spec(activity=SpecActivity(known=True, last_discussion_days=200)), date(2026, 7, 13)
    )
    assert v.pulse is not None
    assert v.pulse.tier == "at-risk"


def test_spec_view_badge_and_pulse_never_contradict_each_other():
    """Invariant: if there are events in the window, activity is at most the
    window length — so Pulse can never claim months of silence."""
    v = spec_view(
        _spec(
            health=SpecHealth(days_since_commit=900),
            activity=SpecActivity(known=True, last_discussion_days=2, events=[_activity_event()]),
        ),
        date(2026, 7, 13),
    )
    assert v.activity.event_count >= 1
    assert v.pulse.tier != "at-risk" or "no activity" not in v.pulse.reason


# ---------------- explicit sort keys ----------------


def test_pulse_sort_key_orders_most_recent_activity_first():
    from mediawg_dashboard.analysis import activity_sort_key

    assert activity_sort_key(1) < activity_sort_key(272)


def test_pulse_sort_key_sinks_unknown_activity():
    from mediawg_dashboard.analysis import activity_sort_key

    assert activity_sort_key(None) > activity_sort_key(10_000)


def test_spec_view_pulse_sort_reflects_the_combined_signal():
    """Regression: sorting used the cell text, so "active" < "blocker open 2309d"
    < "no activity 272d" ordered alphabetically instead of by recency."""
    recent = spec_view(
        _spec(
            health=SpecHealth(days_since_commit=272, oldest_blocking_issue_days=2309),
            activity=SpecActivity(known=True, last_discussion_days=1),
        ),
        date(2026, 7, 13),
    )
    quiet = spec_view(_spec(health=SpecHealth(days_since_commit=272)), date(2026, 7, 13))
    # The at-risk-with-recent-discussion spec sorts above the silent one.
    assert recent.pulse_sort < quiet.pulse_sort


def test_interop_sort_key_ranks_shipped_before_unknown():
    from mediawg_dashboard.analysis import interop_sort_key

    all_shipped = spec_view(
        _spec(interop=InteropStatus(chrome="shipped", firefox="shipped", safari="shipped")),
        date(2026, 7, 13),
    )
    none_known = spec_view(_spec(), date(2026, 7, 13))
    assert all_shipped.interop_sort < none_known.interop_sort
    assert interop_sort_key([]) == 0
