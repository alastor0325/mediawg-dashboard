from datetime import datetime, timezone

from mediawg_dashboard.assemble import build_spec
from mediawg_dashboard.model import HorizontalReviews, InteropStatus, SpecMeta, SpecStatus

NOW = datetime(2026, 7, 13, tzinfo=timezone.utc)


def _meta(**kw):
    base = dict(shortname="webcodecs", title="WebCodecs", repo="w3c/webcodecs", w3c_shortname="webcodecs", wpt_path="/webcodecs/")
    base.update(kw)
    return SpecMeta(**base)


def _issue(labels, created="2026-01-01T00:00:00Z", pr=False):
    d = {"labels": [{"name": n} for n in labels], "created_at": created}
    if pr:
        d["pull_request"] = {}
    return d


def _commit(date_str, login):
    return {"commit": {"author": {"date": date_str, "name": login}}, "author": {"login": login}}


def test_build_spec_composes_all_layers():
    issues = [
        _issue(["a11y-needs-resolution"], "2026-01-01T00:00:00Z"),
        _issue(["agenda"]),
        _issue([], pr=True),
    ]
    commits = [_commit("2026-07-11T00:00:00Z", "ed1"), _commit("2026-07-01T00:00:00Z", "ed2")]
    wpt = {"all_engines_wpt": 74.0, "wpt_test_count": 612}
    support = InteropStatus(chrome="shipped", firefox="shipped", safari="partial")
    # Horizontal review reflects only whether the review was performed (request
    # repo). Needs-resolution issues are a SEPARATE axis (cr_blocking), not folded in.
    horizontal = HorizontalReviews(a11y="requested", tag="resolved")

    spec = build_spec(
        _meta(charter_target="CR Q1 2026"), SpecStatus(stage="WD"), issues, commits, wpt, support, NOW, horizontal
    )

    assert spec.stats.open_issues_count == 2  # PR excluded
    assert spec.stats.open_prs_count == 1
    # Review states pass through from the request-repo data unchanged.
    assert spec.milestones.horizontal.a11y == "requested"
    assert spec.milestones.horizontal.tag == "resolved"
    # The a11y-needs-resolution issue is counted as a CR blocker, separately.
    assert spec.milestones.cr_blocking_issues_open == 1
    assert spec.interop.all_engines_wpt == 74.0
    assert spec.interop.safari == "partial"
    assert spec.health.days_since_activity == 2
    # Both commits (2026-07-11, 2026-07-01) fall in the July bucket.
    assert dict(spec.health.commit_months)["2026-07"] == 2
    assert len(spec.health.commit_months) == 6
    assert spec.health.charter_overdue is True  # CR Q1 2026 past, still WD


def test_build_spec_horizontal_defaults_unknown_when_omitted():
    spec = build_spec(_meta(), SpecStatus(stage="unknown"), [], [], None, InteropStatus(), NOW)
    assert spec.stats.open_issues_count == 0
    assert spec.interop.all_engines_wpt is None
    assert spec.health.days_since_activity is None
    assert spec.milestones.horizontal.a11y == "unknown"


def test_build_spec_issues_none_means_unknown_not_zero():
    # A failed GitHub fetch (issues=None) must render as unknown, not a real 0.
    spec = build_spec(_meta(), SpecStatus(stage="WD"), None, [], None, InteropStatus(), NOW)
    assert spec.stats.open_issues_count is None
    assert spec.stats.open_prs_count is None
    assert spec.milestones.cr_blocking_issues_open is None
