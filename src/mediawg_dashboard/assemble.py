"""Compose a full Spec from fetched raw data — pure, so it's unit-testable.

The CLI does the I/O (calling the fetchers) and hands the raw payloads here.
"""

from datetime import datetime

from mediawg_dashboard.activity import ACTIVITY_WINDOW_DAYS, window_start
from mediawg_dashboard.analysis import charter_overdue
from mediawg_dashboard.fetch.github import (
    build_thread_index,
    compute_repo_stats,
    days_since_last_commit,
    extract_comment_events,
    extract_state_events,
    monthly_commit_counts,
    needs_resolution_stats,
)
from mediawg_dashboard.model import (
    HorizontalReviews,
    InteropStatus,
    Registry,
    RegistryMeta,
    RegistryStatus,
    RepoStats,
    Spec,
    SpecActivity,
    SpecHealth,
    SpecMeta,
    SpecMilestones,
    SpecStatus,
)


def build_activity(
    updated_issues: list[dict] | None,
    comments: list[dict] | None,
    review_comments: list[dict] | None,
    now: datetime,
) -> SpecActivity:
    """Fold the three raw activity payloads into one event list (no I/O).

    All three share a single failure key, so **any** of them being ``None``
    marks the whole axis unknown. Reporting a partial count would be worse than
    saying nothing: a comments outage would render as a confident "0 new".
    """
    if updated_issues is None or comments is None or review_comments is None:
        return SpecActivity(window_days=ACTIVITY_WINDOW_DAYS, known=False)
    since = window_start(now)
    index = build_thread_index(updated_issues)
    events = extract_state_events(updated_issues, since) + extract_comment_events(
        comments + review_comments, index, since
    )
    events.sort(key=lambda e: e.at)
    return SpecActivity(window_days=ACTIVITY_WINDOW_DAYS, events=events, known=True)


def build_spec(
    meta: SpecMeta,
    status: SpecStatus,
    issues: list[dict] | None,
    commits: list[dict] | None,
    wpt_scores: dict | None,
    support: InteropStatus,
    now: datetime,
    horizontal: HorizontalReviews | None = None,
    horizontal_urls: dict[str, str] | None = None,
    updated_issues: list[dict] | None = None,
    comments: list[dict] | None = None,
    review_comments: list[dict] | None = None,
) -> Spec:
    """Assemble one Spec from already-fetched raw data (no I/O).

    ``issues`` is ``None`` when the GitHub fetch failed — counts then stay unknown
    (rendered "—"), so a transient outage doesn't look like a real "0".

    ``horizontal`` (+ ``horizontal_urls``) come from the request-repo search (see
    fetch/horizontal.py) and reflect only whether the *review was performed*.
    Any ``*-needs-resolution`` issues the review left are a separate axis, counted
    in ``cr_blocking_issues_open`` (the CR-blocking-issues line) — not folded into
    the review status, since the review itself is done.
    """
    if issues is None:
        stats = RepoStats()  # all-unknown
        nr_count, nr_oldest = None, None
    else:
        stats = compute_repo_stats(issues, now=now)
        nr_count, nr_oldest = needs_resolution_stats(issues, now=now)
    milestones = SpecMilestones(
        horizontal=horizontal or HorizontalReviews(),
        horizontal_urls=horizontal_urls or {},
        cr_blocking_issues_open=nr_count,
    )

    # support carries MDN per-engine states/versions/mdn_url; layer WPT on top.
    per = (wpt_scores or {}).get("per_engine", {})
    interop = support.model_copy(update={
        "all_engines_wpt": (wpt_scores or {}).get("all_engines_wpt"),
        "wpt_test_count": (wpt_scores or {}).get("wpt_test_count"),
        "wpt_chrome": per.get("chrome"),
        "wpt_firefox": per.get("firefox"),
        "wpt_safari": per.get("safari"),
    })

    commits = commits or []
    health = SpecHealth(
        days_since_activity=days_since_last_commit(commits, now=now),
        oldest_blocking_issue_days=nr_oldest,
        charter_target=meta.charter_target,
        charter_overdue=charter_overdue(meta.charter_target, now.date(), status.stage),
        commit_months=monthly_commit_counts(commits, now=now),
    )

    return Spec(
        meta=meta,
        status=status,
        stats=stats,
        milestones=milestones,
        interop=interop,
        health=health,
        activity=build_activity(updated_issues, comments, review_comments, now),
    )


def build_registry(
    meta: RegistryMeta,
    status: RegistryStatus,
    horizontal: HorizontalReviews | None = None,
    horizontal_urls: dict[str, str] | None = None,
) -> Registry:
    """Assemble one Registry (no I/O).

    ``horizontal`` (+ ``horizontal_urls``) come from the request-repo search (see
    fetch/horizontal.py). ``ac_review`` stays unknown — not in public sources.
    """
    milestones = SpecMilestones(
        horizontal=horizontal or HorizontalReviews(),
        horizontal_urls=horizontal_urls or {},
    )
    return Registry(meta=meta, status=status, milestones=milestones)


# --- Last-known-good fallback --------------------------------------------------
#
# When a source fetch fails, keep the previous value instead of showing unknown.
# ``failed`` names which fetches failed this run; each maps to the assembled
# fields it feeds, which we copy from the stored ``prev``. Pure + testable.


def merge_spec(fresh: Spec, prev: Spec | None, failed: set[str]) -> Spec:
    """Fill this run's failed fields from the last-good ``prev`` spec."""
    if prev is None or not failed:
        return fresh
    s = fresh.model_copy(deep=True)
    if "status" in failed and prev.status.stage != "unknown":
        s.status = prev.status.model_copy(deep=True)
    if "issues" in failed:
        s.stats = prev.stats.model_copy(deep=True)
        s.milestones.cr_blocking_issues_open = prev.milestones.cr_blocking_issues_open
        s.health.oldest_blocking_issue_days = prev.health.oldest_blocking_issue_days
    if "commits" in failed:
        s.health.days_since_activity = prev.health.days_since_activity
        s.health.commit_months = list(prev.health.commit_months)
    if "support" in failed:
        for f in ("chrome", "firefox", "safari", "chrome_version",
                  "firefox_version", "safari_version", "mdn_url", "interop_focus_year"):
            setattr(s.interop, f, getattr(prev.interop, f))
    if "wpt" in failed:
        for f in ("all_engines_wpt", "wpt_test_count", "wpt_chrome", "wpt_firefox", "wpt_safari"):
            setattr(s.interop, f, getattr(prev.interop, f))
    if "horizontal" in failed:
        s.milestones.horizontal = prev.milestones.horizontal.model_copy(deep=True)
        s.milestones.horizontal_urls = dict(prev.milestones.horizontal_urls)
    if "activity" in failed:
        # Events carry their own timestamps, so a kept list re-filters against
        # this run's window and decays naturally instead of freezing.
        s.activity = prev.activity.model_copy(deep=True)
    return s


def merge_registry(fresh: Registry, prev: Registry | None, failed: set[str]) -> Registry:
    """Fill this run's failed fields from the last-good ``prev`` registry."""
    if prev is None or not failed:
        return fresh
    r = fresh.model_copy(deep=True)
    if "status" in failed and prev.status.stage != "unknown":
        r.status = prev.status.model_copy(deep=True)
    if "horizontal" in failed:
        r.milestones.horizontal = prev.milestones.horizontal.model_copy(deep=True)
        r.milestones.horizontal_urls = dict(prev.milestones.horizontal_urls)
    return r
