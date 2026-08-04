"""Activity fetch layer (P7b): pure event extraction + the three `since` fetchers."""

from datetime import datetime, timedelta, timezone

import httpx

from mediawg_dashboard.fetch.github import (
    build_thread_index,
    extract_comment_events,
    extract_state_events,
    fetch_issue_comments,
    fetch_review_comments,
    fetch_updated_issues,
    thread_number,
)

NOW = datetime(2026, 8, 4, 12, 0, tzinfo=timezone.utc)
SINCE = NOW - timedelta(days=7)


def _stamp(days_ago: float) -> str:
    return (NOW - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _issue(
    number: int,
    created_days_ago: float = 100,
    closed_days_ago: float | None = None,
    merged_days_ago: float | None = None,
    is_pr: bool = False,
    author: str = "alice",
    title: str | None = None,
) -> dict:
    out: dict = {
        "number": number,
        "title": title or f"thread {number}",
        "html_url": f"https://github.com/w3c/x/issues/{number}",
        "created_at": _stamp(created_days_ago),
        "closed_at": _stamp(closed_days_ago) if closed_days_ago is not None else None,
        "state": "closed" if closed_days_ago is not None else "open",
        "user": {"login": author},
    }
    if is_pr:
        out["pull_request"] = {
            "merged_at": _stamp(merged_days_ago) if merged_days_ago is not None else None
        }
    return out


def _comment(number: int, days_ago: float = 1, author: str = "bob", pr_review: bool = False) -> dict:
    key = "pull_request_url" if pr_review else "issue_url"
    return {
        key: f"https://api.github.com/repos/w3c/x/issues/{number}",
        "created_at": _stamp(days_ago),
        "user": {"login": author},
    }


# --- thread_number ------------------------------------------------------------


def test_thread_number_from_issue_url():
    assert thread_number(_comment(42)) == 42


def test_thread_number_from_pull_request_url():
    """PR *review* comments carry pull_request_url, not issue_url. Regression
    guard: keying only on issue_url silently drops every review comment."""
    assert thread_number(_comment(42, pr_review=True)) == 42


def test_thread_number_none_when_unparseable():
    assert thread_number({}) is None
    assert thread_number({"issue_url": "https://api.github.com/repos/w3c/x/issues/"}) is None


# --- build_thread_index -------------------------------------------------------


def test_build_thread_index_keys_by_number():
    index = build_thread_index([_issue(1), _issue(2)])
    assert set(index) == {1, 2}


def test_build_thread_index_skips_entries_without_a_number():
    assert build_thread_index([{"title": "junk"}]) == {}


# --- extract_state_events -----------------------------------------------------


def test_extract_state_events_detects_opened_in_window():
    events = extract_state_events([_issue(1, created_days_ago=2)], SINCE)
    assert [e.event for e in events] == ["opened"]
    assert events[0].author == "alice"
    assert events[0].kind == "issue"


def test_extract_state_events_ignores_opened_before_window():
    assert extract_state_events([_issue(1, created_days_ago=30)], SINCE) == []


def test_extract_state_events_detects_closed_in_window():
    events = extract_state_events([_issue(1, closed_days_ago=3)], SINCE)
    assert [e.event for e in events] == ["closed"]
    assert events[0].state == "closed"


def test_extract_state_events_detects_merged_for_a_pr():
    events = extract_state_events(
        [_issue(1, is_pr=True, closed_days_ago=3, merged_days_ago=3)], SINCE
    )
    assert [e.event for e in events] == ["merged"]
    assert events[0].kind == "pr"
    assert events[0].state == "merged"


def test_extract_state_events_merged_does_not_also_count_as_closed():
    """A merged PR is also closed; counting both would inflate the badge."""
    events = extract_state_events(
        [_issue(1, is_pr=True, closed_days_ago=2, merged_days_ago=2)], SINCE
    )
    assert len(events) == 1


def test_extract_state_events_unmerged_closed_pr_counts_as_closed():
    events = extract_state_events([_issue(1, is_pr=True, closed_days_ago=2)], SINCE)
    assert [e.event for e in events] == ["closed"]


def test_extract_state_events_opened_and_merged_both_count():
    events = extract_state_events(
        [_issue(1, is_pr=True, created_days_ago=4, closed_days_ago=1, merged_days_ago=1)], SINCE
    )
    assert sorted(e.event for e in events) == ["merged", "opened"]


def test_extract_state_events_ignores_close_before_window():
    assert extract_state_events([_issue(1, closed_days_ago=30)], SINCE) == []


def test_extract_state_events_tolerates_missing_fields():
    assert extract_state_events([{"number": 1}], SINCE) == []


# --- extract_comment_events ---------------------------------------------------


def test_extract_comment_events_resolves_title_from_the_index():
    index = build_thread_index([_issue(7, title="Clarify colorSpace")])
    events = extract_comment_events([_comment(7)], index, SINCE)
    assert len(events) == 1
    assert events[0].title == "Clarify colorSpace"
    assert events[0].event == "comment"
    assert events[0].author == "bob"
    assert events[0].url.endswith("/7")


def test_extract_comment_events_handles_pr_review_comments():
    index = build_thread_index([_issue(7, is_pr=True)])
    events = extract_comment_events([_comment(7, pr_review=True)], index, SINCE)
    assert len(events) == 1
    assert events[0].kind == "pr"


def test_extract_comment_events_skips_unresolvable_threads():
    """No title = no honest row. Skipping keeps the badge equal to the list's sum
    (only reachable past the _MAX_PAGES pagination cap, which warns separately)."""
    assert extract_comment_events([_comment(999)], {}, SINCE) == []


def test_extract_comment_events_ignores_comments_before_window():
    index = build_thread_index([_issue(7)])
    assert extract_comment_events([_comment(7, days_ago=30)], index, SINCE) == []


def test_extract_comment_events_counts_each_comment_separately():
    index = build_thread_index([_issue(7)])
    events = extract_comment_events([_comment(7), _comment(7), _comment(7)], index, SINCE)
    assert len(events) == 3


# --- the three fetchers -------------------------------------------------------


def _capture() -> tuple[list[httpx.Request], httpx.MockTransport]:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=[{"number": 1}])

    return seen, httpx.MockTransport(handler)


def test_fetch_updated_issues_asks_for_all_states_and_since():
    seen, transport = _capture()
    with httpx.Client(transport=transport) as client:
        fetch_updated_issues("w3c/x", SINCE, client=client)
    url = seen[0].url
    # state=all matters: the default (open) would drop threads closed this week.
    assert url.params["state"] == "all"
    assert url.params["sort"] == "updated"
    assert url.params["since"].startswith("2026-07-28")
    assert "/repos/w3c/x/issues" in str(url)


def test_fetch_issue_comments_hits_the_repo_level_comments_endpoint():
    seen, transport = _capture()
    with httpx.Client(transport=transport) as client:
        fetch_issue_comments("w3c/x", SINCE, client=client)
    assert "/repos/w3c/x/issues/comments" in str(seen[0].url)
    assert seen[0].url.params["since"].startswith("2026-07-28")


def test_fetch_review_comments_hits_the_pulls_comments_endpoint():
    seen, transport = _capture()
    with httpx.Client(transport=transport) as client:
        fetch_review_comments("w3c/x", SINCE, client=client)
    assert "/repos/w3c/x/pulls/comments" in str(seen[0].url)


def test_activity_fetchers_follow_pagination():
    pages: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        pages.append(str(request.url))
        if "page=2" in str(request.url):
            return httpx.Response(200, json=[{"number": 2}])
        return httpx.Response(
            200,
            json=[{"number": 1}],
            headers={"Link": '<https://api.github.com/x?page=2>; rel="next"'},
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        items = fetch_issue_comments("w3c/x", SINCE, client=client)
    assert len(items) == 2


# --- last discussion (unbounded — not limited to the activity window) ---------


def test_days_since_last_discussion_uses_the_newest_updated_at():
    items = [{"updated_at": _stamp(3)}, {"updated_at": _stamp(20)}]
    from mediawg_dashboard.fetch.github import days_since_last_discussion

    assert days_since_last_discussion(items, now=NOW) == 3


def test_days_since_last_discussion_none_when_repo_has_no_threads():
    from mediawg_dashboard.fetch.github import days_since_last_discussion

    assert days_since_last_discussion([], now=NOW) is None


def test_days_since_last_discussion_tolerates_missing_field():
    from mediawg_dashboard.fetch.github import days_since_last_discussion

    assert days_since_last_discussion([{"number": 1}], now=NOW) is None


def test_fetch_last_discussion_asks_for_one_newest_thread_unfiltered():
    """No `since`: the whole point is to see past the activity window, so a
    comment 30 days ago still counts as activity."""
    seen, transport = _capture()
    from mediawg_dashboard.fetch.github import fetch_last_discussion

    with httpx.Client(transport=transport) as client:
        fetch_last_discussion("w3c/x", client=client)
    url = seen[0].url
    assert url.params["state"] == "all"
    assert url.params["sort"] == "updated"
    assert url.params["direction"] == "desc"
    assert url.params["per_page"] == "1"
    assert "since" not in url.params
