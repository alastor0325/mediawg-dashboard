from datetime import date

from mediawg_dashboard.model import RepoStats, Spec, SpecMeta, SpecStatus
from mediawg_dashboard.render import render_index


def _spec(shortname: str = "webcodecs", stage: str = "WD") -> Spec:
    return Spec(
        meta=SpecMeta(
            shortname=shortname,
            title=shortname.title(),
            repo=f"w3c/{shortname}",
            w3c_shortname=shortname,
            tr_url=f"https://www.w3.org/TR/{shortname}/",
        ),
        status=SpecStatus(
            stage=stage,
            last_tr_publication=date(2026, 5, 5),
            ed_url=f"https://w3c.github.io/{shortname}/",
        ),
        stats=RepoStats(open_issues_count=42, open_prs_count=5, oldest_open_issue_age_days=180),
    )


def test_render_returns_html_string():
    html = render_index([_spec()])
    assert html.startswith("<!doctype html>") or html.startswith("<!DOCTYPE html>")
    assert "</html>" in html


def test_render_includes_spec_title():
    html = render_index([_spec("mediasession")])
    assert "Mediasession" in html


def test_render_includes_stage():
    html = render_index([_spec(stage="CR-snapshot")])
    assert "CR-snapshot" in html


def test_render_includes_open_issue_count():
    html = render_index([_spec()])
    assert "42" in html


def test_render_handles_multiple_specs():
    html = render_index([_spec("a"), _spec("b"), _spec("c")])
    assert "A" in html and "B" in html and "C" in html


def test_render_empty_list():
    html = render_index([])
    assert "<html" in html.lower()


def test_render_links_to_repo():
    html = render_index([_spec("webcodecs")])
    assert "https://github.com/w3c/webcodecs" in html


def test_render_links_to_tr():
    html = render_index([_spec("webcodecs")])
    assert "https://www.w3.org/TR/webcodecs/" in html
