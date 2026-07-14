"""Compose a full Spec from fetched raw data — pure, so it's unit-testable.

The CLI does the I/O (calling the fetchers) and hands the raw payloads here.
"""

from datetime import datetime

from mediawg_dashboard.analysis import charter_overdue
from mediawg_dashboard.fetch.github import (
    compute_repo_stats,
    days_since_last_commit,
    needs_resolution_stats,
    parse_horizontal_reviews,
)
from mediawg_dashboard.model import (
    InteropStatus,
    Spec,
    SpecHealth,
    SpecMeta,
    SpecMilestones,
    SpecStatus,
)


def build_spec(
    meta: SpecMeta,
    status: SpecStatus,
    issues: list[dict],
    commits: list[dict],
    wpt_scores: dict | None,
    support: InteropStatus,
    now: datetime,
) -> Spec:
    """Assemble one Spec from already-fetched raw data (no I/O)."""
    stats = compute_repo_stats(issues, now=now)

    nr_count, nr_oldest = needs_resolution_stats(issues, now=now)
    milestones = SpecMilestones(
        horizontal=parse_horizontal_reviews(issues),
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
