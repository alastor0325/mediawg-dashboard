from datetime import datetime, timedelta, timezone

import httpx

from mediawg_dashboard.fetch.github import (
    _fetch_all_pages,
    classify_issues_and_prs,
    compute_oldest_issue_age_days,
)


def _issue(number: int, created_days_ago: int = 10, is_pr: bool = False) -> dict:
    created_at = datetime.now(timezone.utc) - timedelta(days=created_days_ago)
    out: dict = {
        "number": number,
        "title": f"issue {number}",
        "created_at": created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "state": "open",
    }
    if is_pr:
        out["pull_request"] = {"url": f"https://api.github.com/.../pulls/{number}"}
    return out


def test_classify_separates_issues_from_prs():
    items = [
        _issue(1, is_pr=False),
        _issue(2, is_pr=True),
        _issue(3, is_pr=False),
        _issue(4, is_pr=True),
        _issue(5, is_pr=True),
    ]
    issues, prs = classify_issues_and_prs(items)
    assert len(issues) == 2
    assert len(prs) == 3
    assert {i["number"] for i in issues} == {1, 3}
    assert {p["number"] for p in prs} == {2, 4, 5}


def test_classify_empty_list():
    issues, prs = classify_issues_and_prs([])
    assert issues == []
    assert prs == []


def test_oldest_age_returns_largest_age():
    issues = [
        _issue(1, created_days_ago=5),
        _issue(2, created_days_ago=50),
        _issue(3, created_days_ago=20),
    ]
    age = compute_oldest_issue_age_days(issues)
    assert age == 50


def test_oldest_age_empty_returns_none():
    assert compute_oldest_issue_age_days([]) is None


def test_oldest_age_single_issue():
    issues = [_issue(1, created_days_ago=7)]
    assert compute_oldest_issue_age_days(issues) == 7


def test_fetch_all_pages_preserves_next_url_query_string():
    # Regression: passing params={} to httpx strips the URL's existing query
    # string. We must drop params entirely (or pass None) on follow-up pages.
    captured_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_urls.append(str(request.url))
        if "page=2" in str(request.url):
            return httpx.Response(200, json=[{"number": 2}])
        # Page 1: include a Link header pointing at a fully-qualified next URL.
        next_url = "https://api.example.com/items?state=open&per_page=100&page=2"
        return httpx.Response(
            200,
            json=[{"number": 1}],
            headers={"Link": f'<{next_url}>; rel="next"'},
        )

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        items = _fetch_all_pages(
            client,
            "https://api.example.com/items",
            {"state": "open", "per_page": 100},
        )

    assert [i["number"] for i in items] == [1, 2]
    # Second call must preserve the next_url's query string.
    assert "page=2" in captured_urls[1]
    assert "state=open" in captured_urls[1]


def test_fetch_all_pages_terminates_without_next_link():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"number": 1}, {"number": 2}])

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        items = _fetch_all_pages(client, "https://api.example.com/items", {})
    assert len(items) == 2
