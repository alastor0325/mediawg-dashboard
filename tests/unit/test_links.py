from mediawg_dashboard.links import (
    horizontal_request_url,
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


def test_horizontal_request_url_targets_the_groups_request_repo():
    url = horizontal_request_url("a11y", "Autoplay Policy Detection")
    assert "w3c/a11y-request/issues" in url
    assert "Autoplay%20Policy%20Detection" in url
    assert "in%3Atitle" in url


def test_horizontal_request_url_unknown_group_is_none():
    assert horizontal_request_url("bogus", "x") is None


def test_hr_review_url():
    assert hr_review_url("webcodecs") == (
        "https://w3c.github.io/horizontal-issue-tracker/review.html?shortname=webcodecs"
    )


def test_repo_issues_url():
    assert repo_issues_url("w3c/webcodecs") == "https://github.com/w3c/webcodecs/issues"


def test_wpt_url_none_when_no_path():
    assert wpt_url(None) is None
    assert wpt_url("/webcodecs/") == "https://wpt.fyi/results/webcodecs/"


def test_rec_snapshot_url_builds_dated_tr_url():
    from mediawg_dashboard.links import rec_snapshot_url

    assert rec_snapshot_url("encrypted-media", "2017-09-18") == (
        "https://www.w3.org/TR/2017/REC-encrypted-media-20170918/"
    )
    assert rec_snapshot_url("media-source", "2016-11-17") == (
        "https://www.w3.org/TR/2016/REC-media-source-20161117/"
    )
    assert rec_snapshot_url("x", "not-a-date") is None
