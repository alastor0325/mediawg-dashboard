from mediawg_dashboard.links import (
    horizontal_group_url,
    hr_review_url,
    issues_search_url,
    needs_resolution_url,
    repo_issues_url,
    wpt_url,
)


def test_issues_search_url_encodes_query():
    url = issues_search_url("w3c/webcodecs", "is:open label:x")
    assert url.startswith("https://github.com/w3c/webcodecs/issues?q=")
    assert "is%3Aopen" in url


def test_needs_resolution_url_lists_all_groups():
    url = needs_resolution_url("w3c/webcodecs")
    for g in ("a11y", "i18n", "privacy", "security", "tag"):
        assert f"{g}-needs-resolution" in url


def test_horizontal_group_url_includes_tracker_and_needs_resolution():
    url = horizontal_group_url("w3c/webcodecs", "a11y")
    assert "a11y-needs-resolution" in url
    assert "a11y-tracker" in url
    # No is:open — resolved (closed) reviews should still show.
    assert "is%3Aopen" not in url


def test_hr_review_url():
    assert hr_review_url("webcodecs") == (
        "https://w3c.github.io/horizontal-issue-tracker/review.html?shortname=webcodecs"
    )


def test_repo_issues_url():
    assert repo_issues_url("w3c/webcodecs") == "https://github.com/w3c/webcodecs/issues"


def test_wpt_url_none_when_no_path():
    assert wpt_url(None) is None
    assert wpt_url("/webcodecs/") == "https://wpt.fyi/results/webcodecs/"
