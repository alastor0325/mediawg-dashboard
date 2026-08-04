"""Pure "new this week" digest: fold raw activity events into display threads.

No I/O. The window is computed at build time (the page is a static daily build),
so every viewer sees the same "this week" — stated explicitly in the UI as a
date, since "this week" alone would be ambiguous on a page rebuilt daily.

The badge counts **events** (each comment, each state change) while the list
shows one row per **thread**, so the two numbers legitimately differ; the strip
header reconciles them ("7 updates in 4 threads").
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime, timedelta

from mediawg_dashboard.model import (
    ACTIVITY_WINDOW_DAYS,
    ActivityDigest,
    ActivityEvent,
    ActivityThread,
    SpecActivity,
)

# ACTIVITY_WINDOW_DAYS is defined in model.py (so the stored default can't drift
# from the window used here) and re-exported: the fetchers' `since` and the
# view's re-filter must agree, or a stale event could outlive its own window.
__all__ = [
    "ACTIVITY_WINDOW_DAYS",
    "MAX_THREADS",
    "activity_digest",
    "format_ago",
    "format_authors",
    "group_activity",
    "thread_summary",
    "window_start",
]

# Threads shown in the panel before collapsing the rest into "+N more".
MAX_THREADS = 8

# State changes, most→least significant. A merged PR is also closed, so the
# summary reports only the strongest one rather than double-counting.
_STATE_RANK = ("merged", "closed", "opened")


def window_start(now: datetime, days: int = ACTIVITY_WINDOW_DAYS) -> datetime:
    """The inclusive lower bound of the activity window (the fetchers' `since`)."""
    return now - timedelta(days=days)


def format_ago(days: int) -> str:
    """Recency for a thread row: 'today' / '1d ago' / '6d ago'."""
    if days <= 0:
        return "today"
    return f"{days}d ago"


def format_authors(events: Iterable[ActivityEvent], cap: int = 2) -> str:
    """Participants as bare handles, e.g. 'alice, bob +1' ('' if none known).

    Ordered by **first appearance in the window** — deterministic and unranked,
    so the dashboard never implies who matters most (neutrality rule).
    """
    seen: list[str] = []
    for event in sorted(events, key=lambda e: e.at):
        if event.author and event.author not in seen:
            seen.append(event.author)
    if not seen:
        return ""
    shown = ", ".join(seen[:cap])
    remainder = len(seen) - cap
    return f"{shown} +{remainder}" if remainder > 0 else shown


def thread_summary(events: Iterable[ActivityEvent]) -> str:
    """What happened on one thread, e.g. 'opened · 3 comments' / 'merged'."""
    events = list(events)
    parts: list[str] = []
    states = {e.event for e in events}
    for state in _STATE_RANK:
        if state in states:
            parts.append(state)
            break
    comments = sum(1 for e in events if e.event == "comment")
    if comments:
        parts.append(f"{comments} comment{'s' if comments > 1 else ''}")
    return " · ".join(parts)


def group_activity(
    events: Iterable[ActivityEvent],
    since: date,
    today: date,
    limit: int = MAX_THREADS,
) -> ActivityDigest:
    """Fold events into newest-first threads, capped at ``limit``.

    Events older than ``since`` are dropped, so a last-known-good list decays
    against a fresh window instead of showing stale rows forever. The counts
    describe **all** in-window activity, not just the shown threads — the cap is
    a display limit, never a silent truncation of the numbers.
    """
    by_thread: dict[tuple[str, int], list[ActivityEvent]] = {}
    total = 0
    for event in events:
        if event.at.date() < since:
            continue
        total += 1
        by_thread.setdefault((event.kind, event.number), []).append(event)

    # (newest event timestamp, thread) — sorting on the timestamp rather than the
    # day-granular days_ago keeps same-day threads in true newest-first order.
    dated: list[tuple[datetime, ActivityThread]] = []
    for group in by_thread.values():
        group.sort(key=lambda e: e.at)
        newest = group[-1]  # titles get edited — the latest one is current
        days_ago = (today - newest.at.date()).days
        dated.append((
            newest.at,
            ActivityThread(
                number=newest.number,
                kind=newest.kind,
                title=newest.title,
                url=newest.url,
                event_count=len(group),
                summary=thread_summary(group),
                authors=format_authors(group),
                days_ago=days_ago,
                ago=format_ago(days_ago),
            ),
        ))
    dated.sort(key=lambda pair: pair[0], reverse=True)
    threads = [thread for _, thread in dated]

    return ActivityDigest(
        threads=threads[:limit],
        event_count=total,
        thread_count=len(threads),
        overflow=max(0, len(threads) - limit),
        since=since,
    )


def activity_digest(
    activity: SpecActivity, today: date, limit: int = MAX_THREADS
) -> ActivityDigest | None:
    """The digest for one spec, or None when activity is unknown.

    None (fetch failed, no last-good) must render "—" and suppress the badge;
    a known-but-empty window is a real ``0``. Unknown ≠ zero.
    """
    if not activity.known:
        return None
    return group_activity(
        activity.events,
        since=today - timedelta(days=activity.window_days),
        today=today,
        limit=limit,
    )
