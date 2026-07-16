"""Compose a full Spec from fetched raw data — pure, so it's unit-testable.

The CLI does the I/O (calling the fetchers) and hands the raw payloads here.
"""

from datetime import datetime

from mediawg_dashboard.analysis import charter_overdue
from mediawg_dashboard.fetch.github import (
    compute_repo_stats,
    days_since_last_commit,
    needs_resolution_by_group,
    needs_resolution_stats,
)
from mediawg_dashboard.model import (
    HorizontalReviews,
    InteropStatus,
    Registry,
    RegistryMeta,
    RegistryStatus,
    Spec,
    SpecHealth,
    SpecMeta,
    SpecMilestones,
    SpecStatus,
)

_HR_GROUPS = ("a11y", "i18n", "privacy", "security", "tag")


def _merge_horizontal(
    reviews: HorizontalReviews, urls: dict[str, str], issues: list[dict]
) -> tuple[HorizontalReviews, dict[str, str]]:
    """Overlay the spec repo's open ``*-needs-resolution`` issues onto the
    request-repo review states: an open needs-resolution means the review raised
    a blocking concern that's still unresolved -> 'open' (even if the review
    request was closed), deep-linked to that issue.
    """
    nr = needs_resolution_by_group(issues)
    states: dict[str, str] = {}
    merged_urls = dict(urls)
    for group in _HR_GROUPS:
        if group in nr:
            states[group] = "open"
            html_url = nr[group].get("html_url")
            if html_url:
                merged_urls[group] = html_url
        else:
            states[group] = getattr(reviews, group)
    return HorizontalReviews(**states), merged_urls


def build_spec(
    meta: SpecMeta,
    status: SpecStatus,
    issues: list[dict],
    commits: list[dict],
    wpt_scores: dict | None,
    support: InteropStatus,
    now: datetime,
    horizontal: HorizontalReviews | None = None,
    horizontal_urls: dict[str, str] | None = None,
) -> Spec:
    """Assemble one Spec from already-fetched raw data (no I/O).

    ``horizontal`` (+ ``horizontal_urls``) come from the request-repo search (see
    fetch/horizontal.py) — not from the spec repo's own labels, which are empty.
    """
    stats = compute_repo_stats(issues, now=now)

    nr_count, nr_oldest = needs_resolution_stats(issues, now=now)
    merged_reviews, merged_urls = _merge_horizontal(
        horizontal or HorizontalReviews(), horizontal_urls or {}, issues
    )
    milestones = SpecMilestones(
        horizontal=merged_reviews,
        horizontal_urls=merged_urls,
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
