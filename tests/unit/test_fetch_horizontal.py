"""Unit tests for the horizontal-review request-repo fetcher (pure parts)."""

from mediawg_dashboard.fetch.horizontal import (
    HR_REQUEST_REPOS,
    _repo_full_name,
    _review_state,
    classify_reviews,
    hr_search_query,
)


def _item(repo: str, number: int, state: str, pr: bool = False) -> dict:
    d = {
        "repository_url": f"https://api.github.com/repos/{repo}",
        "number": number,
        "state": state,
        "html_url": f"https://github.com/{repo}/issues/{number}",
    }
    if pr:
        d["pull_request"] = {}
    return d


def test_hr_search_query_covers_all_five_repos():
    q = hr_search_query("Autoplay Policy Detection")
    assert '"Autoplay Policy Detection" in:title' in q
    assert "is:issue" in q
    for repo in HR_REQUEST_REPOS.values():
        assert f"repo:{repo}" in q


def test_repo_full_name_extracts_owner_repo():
    assert _repo_full_name("https://api.github.com/repos/w3c/a11y-request") == "w3c/a11y-request"
    assert _repo_full_name("garbage") == ""


def test_review_state_closed_is_resolved_open_is_requested():
    assert _review_state({"state": "closed"}) == "resolved"
    assert _review_state({"state": "open"}) == "requested"


def test_classify_reviews_autoplay_like():
    # Mirrors the real autoplay data: 4 closed reviews + a11y still open.
    items = [
        _item("w3c/a11y-request", 39, "open"),
        _item("w3c/security-request", 48, "closed"),
        _item("w3ctag/design-reviews", 810, "closed"),
        _item("w3cping/privacy-request", 111, "closed"),
        _item("w3c/i18n-request", 192, "closed"),
    ]
    res = classify_reviews(items)
    assert res.reviews.a11y == "requested"
    assert res.reviews.security == "resolved"
    assert res.reviews.tag == "resolved"
    assert res.reviews.privacy == "resolved"
    assert res.reviews.i18n == "resolved"
    # Each state carries the actual request-issue URL for the chip to link to.
    assert res.urls["a11y"] == "https://github.com/w3c/a11y-request/issues/39"
    assert res.urls["tag"] == "https://github.com/w3ctag/design-reviews/issues/810"


def test_classify_reviews_missing_group_is_unknown():
    res = classify_reviews([_item("w3c/i18n-request", 1, "closed")])
    assert res.reviews.i18n == "resolved"
    assert res.reviews.a11y == "unknown"
    assert res.reviews.tag == "unknown"
    assert "a11y" not in res.urls  # no issue -> no link


def test_classify_reviews_uses_most_recent_issue_per_group():
    # Two TAG issues: older closed (overtaken), newer open (current review) -> requested.
    items = [
        _item("w3ctag/design-reviews", 356, "closed"),
        _item("w3ctag/design-reviews", 900, "open"),
    ]
    res = classify_reviews(items)
    assert res.reviews.tag == "requested"
    assert res.urls["tag"].endswith("/900")  # links to the current review


def test_classify_reviews_ignores_prs_and_unknown_repos():
    items = [
        _item("w3c/security-request", 5, "open", pr=True),  # PR — skip
        _item("w3c/webcodecs", 10, "closed"),  # not a request repo — skip
    ]
    assert classify_reviews(items).reviews.security == "unknown"


def test_classify_reviews_empty_all_unknown():
    res = classify_reviews([])
    assert all(
        getattr(res.reviews, g) == "unknown" for g in ("a11y", "i18n", "privacy", "security", "tag")
    )
    assert res.urls == {}
