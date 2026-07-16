from datetime import datetime, timezone

from mediawg_dashboard.fetch.github import (
    count_labeled,
    days_since_last_commit,
    needs_resolution_stats,
)
from mediawg_dashboard.fetch.support import bcd_file_url, parse_bcd_support
from mediawg_dashboard.fetch.wpt import parse_wpt_scores

NOW = datetime(2026, 7, 13, tzinfo=timezone.utc)


def _issue(labels, created="2026-01-01T00:00:00Z"):
    return {"labels": [{"name": n} for n in labels], "created_at": created}


def test_count_labeled():
    issues = [_issue(["agenda"]), _issue(["agenda"]), _issue(["x"])]
    assert count_labeled(issues, "agenda") == 2


def test_needs_resolution_stats():
    issues = [
        _issue(["security-needs-resolution"], "2026-01-01T00:00:00Z"),
        _issue(["i18n-needs-resolution"], "2026-06-01T00:00:00Z"),
        _issue(["agenda"]),
    ]
    count, oldest = needs_resolution_stats(issues, now=NOW)
    assert count == 2
    assert oldest == (NOW - datetime(2026, 1, 1, tzinfo=timezone.utc)).days


def test_needs_resolution_stats_none():
    assert needs_resolution_stats([], now=NOW) == (0, None)


# ---------- commit signals ----------


def _commit(date_str, login=None, name="Ed"):
    return {"commit": {"author": {"date": date_str, "name": name}}, "author": {"login": login} if login else None}


def test_days_since_last_commit():
    commits = [_commit("2026-07-11T00:00:00Z"), _commit("2026-05-01T00:00:00Z")]
    assert days_since_last_commit(commits, now=NOW) == 2


def test_days_since_last_commit_none():
    assert days_since_last_commit([], now=NOW) is None


# ---------- wpt scoring ----------


def test_parse_wpt_scores_per_engine_counts():
    payload = {
        "runs": [{"browser_name": "chrome"}, {"browser_name": "firefox"}, {"browser_name": "safari"}],
        "results": [
            {"test": "/x/a.html", "legacy_status": [{"passes": 5, "total": 5}, {"passes": 5, "total": 5}, {"passes": 5, "total": 5}]},
            {"test": "/x/b.html", "legacy_status": [{"passes": 4, "total": 5}, {"passes": 5, "total": 5}, {"passes": 5, "total": 5}]},
        ],
    }
    out = parse_wpt_scores(payload)
    assert out["wpt_test_count"] == 2
    # Only 1 of 2 tests passes fully in all engines.
    assert out["all_engines_wpt"] == 50.0
    # per-engine is now (passes, total).
    assert out["per_engine"]["chrome"] == (9, 10)
    assert out["per_engine"]["firefox"] == (10, 10)


def test_parse_wpt_scores_empty():
    out = parse_wpt_scores({"runs": [], "results": []})
    assert out["all_engines_wpt"] is None
    assert out["wpt_test_count"] == 0


# ---------- browser support from MDN BCD ----------


def test_bcd_file_url():
    assert bcd_file_url("api.Navigator.getAutoplayPolicy").endswith("/api/Navigator.json")
    assert bcd_file_url("api.MediaSource").endswith("/api/MediaSource.json")


def _bcd(chrome, firefox, safari, path="api.Feature"):
    return {"api": {"Feature": {"__compat": {
        "mdn_url": "https://developer.mozilla.org/docs/Web/API/Feature",
        "support": {"chrome": chrome, "firefox": firefox, "safari": safari},
    }}}}


def test_parse_bcd_support_versions_and_states():
    data = _bcd({"version_added": "94"}, {"version_added": False}, {"version_added": True})
    interop = parse_bcd_support(data, "api.Feature")
    assert interop.chrome == "shipped" and interop.chrome_version == "94"
    assert interop.firefox == "none"
    assert interop.safari == "shipped" and interop.safari_version is None
    assert interop.mdn_url.endswith("/Feature")


def test_parse_bcd_support_handles_list_flags_and_null():
    data = _bcd(
        [{"version_added": "31"}, {"prefix": "webkit", "version_added": "23"}],
        {"version_added": "63", "flags": [{"name": "x"}]},
        {"version_added": None},
    )
    interop = parse_bcd_support(data, "api.Feature")
    assert interop.chrome == "shipped" and interop.chrome_version == "31"  # first range
    assert interop.firefox == "partial"  # behind a flag
    assert interop.safari == "unknown"


# ---------- wpt fetch (query regression) ----------

import httpx  # noqa: E402

from mediawg_dashboard.fetch.wpt import fetch_wpt_scores  # noqa: E402


def test_fetch_wpt_scores_queries_path_substring_and_parses():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["q"] = request.url.params.get("q")
        return httpx.Response(200, json={
            "runs": [{"browser_name": "chrome"}, {"browser_name": "firefox"}, {"browser_name": "safari"}],
            "results": [{"test": "/webcodecs/a.html", "legacy_status": [
                {"passes": 5, "total": 5}, {"passes": 5, "total": 5}, {"passes": 5, "total": 5}]}],
        })

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        out = fetch_wpt_scores("/webcodecs/", ["1", "2", "3"], client=client)

    # Regression: query must be the bare path (no 'path:' operator).
    assert captured["q"] == "/webcodecs/"
    assert out["wpt_test_count"] == 1
    assert out["all_engines_wpt"] == 100.0


def test_fetch_wpt_scores_no_runs_returns_none():
    assert fetch_wpt_scores("/x/", []) is None
