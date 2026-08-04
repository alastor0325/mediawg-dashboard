"""Unit tests for the pure activity digest (P7a) — no I/O."""

from datetime import date, datetime, timedelta, timezone

from mediawg_dashboard.activity import (
    ACTIVITY_WINDOW_DAYS,
    MAX_THREADS,
    activity_digest,
    format_ago,
    format_authors,
    group_activity,
    thread_summary,
    window_start,
)
from mediawg_dashboard.model import ActivityEvent, SpecActivity

TODAY = date(2026, 8, 4)


def _event(
    number: int = 1,
    event: str = "comment",
    days_ago: int = 1,
    author: str | None = "alice",
    kind: str = "issue",
    title: str | None = None,
    state: str = "open",
) -> ActivityEvent:
    at = datetime(2026, 8, 4, 12, 0, tzinfo=timezone.utc) - timedelta(days=days_ago)
    return ActivityEvent(
        number=number,
        kind=kind,
        title=title or f"thread {number}",
        url=f"https://github.com/w3c/x/issues/{number}",
        state=state,
        event=event,
        author=author,
        at=at,
    )


# --- window / formatting -------------------------------------------------------


def test_window_start_defaults_to_the_configured_window():
    now = datetime(2026, 8, 4, 3, 0, tzinfo=timezone.utc)
    assert window_start(now) == now - timedelta(days=ACTIVITY_WINDOW_DAYS)


def test_window_start_honours_an_explicit_length():
    now = datetime(2026, 8, 4, 3, 0, tzinfo=timezone.utc)
    assert window_start(now, days=14) == now - timedelta(days=14)


def test_format_ago_today_and_days():
    assert format_ago(0) == "today"
    assert format_ago(1) == "1d ago"
    assert format_ago(6) == "6d ago"


def test_format_authors_orders_by_first_appearance_not_alphabetically():
    events = [
        _event(author="zoe", days_ago=5),
        _event(author="alice", days_ago=3),
    ]
    assert format_authors(events) == "zoe, alice"


def test_format_authors_dedupes_repeat_commenters():
    events = [
        _event(author="alice", days_ago=5),
        _event(author="alice", days_ago=2),
    ]
    assert format_authors(events) == "alice"


def test_format_authors_caps_and_counts_the_remainder():
    events = [
        _event(author="a", days_ago=5),
        _event(author="b", days_ago=4),
        _event(author="c", days_ago=3),
        _event(author="d", days_ago=2),
    ]
    assert format_authors(events, cap=2) == "a, b +2"


def test_format_authors_empty_when_no_authors_known():
    assert format_authors([_event(author=None)]) == ""


# --- thread summary -----------------------------------------------------------


def test_thread_summary_counts_comments():
    events = [_event(event="comment"), _event(event="comment")]
    assert thread_summary(events) == "2 comments"


def test_thread_summary_singular_comment():
    assert thread_summary([_event(event="comment")]) == "1 comment"


def test_thread_summary_state_change_leads():
    events = [_event(event="comment"), _event(event="opened", days_ago=3)]
    assert thread_summary(events) == "opened · 1 comment"


def test_thread_summary_state_only():
    assert thread_summary([_event(event="merged")]) == "merged"


def test_thread_summary_merged_wins_over_closed():
    events = [_event(event="closed"), _event(event="merged")]
    assert thread_summary(events) == "merged"


# --- grouping ----------------------------------------------------------------


def test_group_activity_dedupes_to_one_row_per_thread():
    events = [_event(number=1), _event(number=1), _event(number=2)]
    digest = group_activity(events, since=TODAY - timedelta(days=7), today=TODAY)
    assert digest.thread_count == 2
    assert digest.event_count == 3


def test_group_activity_counts_issue_and_pr_numbers_separately():
    events = [_event(number=5, kind="issue"), _event(number=5, kind="pr")]
    digest = group_activity(events, since=TODAY - timedelta(days=7), today=TODAY)
    assert digest.thread_count == 2


def test_group_activity_orders_newest_first():
    events = [_event(number=1, days_ago=6), _event(number=2, days_ago=1)]
    digest = group_activity(events, since=TODAY - timedelta(days=7), today=TODAY)
    assert [t.number for t in digest.threads] == [2, 1]


def test_group_activity_drops_events_outside_the_window():
    """A stale last-known-good list must decay against a fresh window."""
    events = [_event(number=1, days_ago=2), _event(number=2, days_ago=30)]
    digest = group_activity(events, since=TODAY - timedelta(days=7), today=TODAY)
    assert [t.number for t in digest.threads] == [1]
    assert digest.event_count == 1


def test_group_activity_caps_threads_and_reports_overflow():
    events = [_event(number=n, days_ago=1) for n in range(1, 12)]
    digest = group_activity(events, since=TODAY - timedelta(days=7), today=TODAY, limit=8)
    assert len(digest.threads) == 8
    assert digest.overflow == 3
    # The count still reflects every event, not just the shown ones.
    assert digest.event_count == 11
    assert digest.thread_count == 11


def test_group_activity_no_overflow_when_under_the_cap():
    digest = group_activity([_event()], since=TODAY - timedelta(days=7), today=TODAY)
    assert digest.overflow == 0


def test_group_activity_empty_is_a_real_zero_not_none():
    digest = group_activity([], since=TODAY - timedelta(days=7), today=TODAY)
    assert digest.event_count == 0
    assert digest.threads == []


def test_group_activity_thread_carries_title_url_kind_and_days_ago():
    events = [_event(number=9, kind="pr", title="Fix IDL", days_ago=2, state="merged")]
    digest = group_activity(events, since=TODAY - timedelta(days=7), today=TODAY)
    thread = digest.threads[0]
    assert thread.title == "Fix IDL"
    assert thread.kind == "pr"
    assert thread.state == "merged"
    assert thread.days_ago == 2
    assert thread.url.endswith("/9")


def test_group_activity_uses_the_newest_events_title():
    """Titles get edited; the most recent event's title is the current one."""
    events = [
        _event(number=1, title="old title", days_ago=5),
        _event(number=1, title="new title", days_ago=1),
    ]
    digest = group_activity(events, since=TODAY - timedelta(days=7), today=TODAY)
    assert digest.threads[0].title == "new title"


def test_group_activity_since_is_recorded_for_the_ui():
    since = TODAY - timedelta(days=7)
    digest = group_activity([_event()], since=since, today=TODAY)
    assert digest.since == since


# --- activity_digest (the SpecActivity entry point) ---------------------------


def test_activity_digest_returns_none_when_unknown():
    """A failed fetch with no last-good must render '—', never '0'."""
    assert activity_digest(SpecActivity(known=False), TODAY) is None


def test_activity_digest_returns_zero_digest_when_known_and_empty():
    digest = activity_digest(SpecActivity(known=True, events=[]), TODAY)
    assert digest is not None
    assert digest.event_count == 0


def test_activity_digest_uses_the_stored_window_length():
    activity = SpecActivity(known=True, window_days=3, events=[_event(days_ago=5)])
    digest = activity_digest(activity, TODAY)
    # 5 days ago is outside a 3-day window.
    assert digest.event_count == 0


def test_activity_digest_default_cap_is_max_threads():
    events = [_event(number=n) for n in range(1, MAX_THREADS + 4)]
    digest = activity_digest(SpecActivity(known=True, events=events), TODAY)
    assert len(digest.threads) == MAX_THREADS
    assert digest.overflow == 3
