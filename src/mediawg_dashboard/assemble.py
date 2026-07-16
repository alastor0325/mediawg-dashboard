"""Compose a full Spec from fetched raw data — pure, so it's unit-testable.

The CLI does the I/O (calling the fetchers) and hands the raw payloads here.
"""

from datetime import datetime

from mediawg_dashboard.analysis import charter_overdue
from mediawg_dashboard.fetch.github import (
    compute_repo_stats,
    days_since_last_commit,
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
    SpecHealth,
    SpecMeta,
    SpecMilestones,
    SpecStatus,
)


def build_spec(
    meta: SpecMeta,
    status: SpecStatus,
    issues: list[dict] | None,
    commits: list[dict],
    wpt_scores: dict | None,
    support: InteropStatus,
    now: datetime,
    horizontal: HorizontalReviews | None = None,
    horizontal_urls: dict[str, str] | None = None,
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

    health = SpecHealth(
        days_since_activity=days_since_last_commit(commits, now=now),
        oldest_blocking_issue_days=nr_oldest,
        charter_target=meta.charter_target,
        charter_overdue=charter_overdue(meta.charter_target, now.date(), status.stage),
        commit_months=monthly_commit_counts(commits, now=now),
    )

    return Spec(meta=meta, status=status, stats=stats, milestones=milestones, interop=interop, health=health)


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
