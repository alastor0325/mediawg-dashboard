from datetime import date

from mediawg_dashboard.model import (
    HorizontalReviews,
    InteropStatus,
    Registry,
    RegistryMeta,
    RegistryStatus,
    RepoStats,
    Spec,
    SpecMeta,
    SpecMilestones,
    SpecStatus,
)
from mediawg_dashboard.render import render_index, summarize_registries


def _registry(
    shortname: str = "webcodecs-codec-registry",
    stage: str = "Registry Draft",
    entry_count: int | None = 13,
    horizontal: HorizontalReviews | None = None,
) -> Registry:
    return Registry(
        meta=RegistryMeta(
            shortname=shortname,
            title=shortname.replace("-", " ").title(),
            parent="WebCodecs",
            repo="w3c/webcodecs",
            w3c_shortname=shortname,
            tr_url=f"https://www.w3.org/TR/{shortname}/",
            entry_count=entry_count,
        ),
        status=RegistryStatus(stage=stage, last_published=date(2026, 2, 12)),
        milestones=SpecMilestones(horizontal=horizontal or HorizontalReviews()),
    )


def _spec(
    shortname: str = "webcodecs",
    stage: str = "WD",
    wpt_path: str | None = "/webcodecs/",
    interop: InteropStatus | None = None,
) -> Spec:
    return Spec(
        meta=SpecMeta(
            shortname=shortname,
            title=shortname.title(),
            repo=f"w3c/{shortname}",
            w3c_shortname=shortname,
            tr_url=f"https://www.w3.org/TR/{shortname}/",
            wpt_path=wpt_path,
        ),
        status=SpecStatus(
            stage=stage,
            last_tr_publication=date(2026, 5, 5),
            ed_url=f"https://w3c.github.io/{shortname}/",
        ),
        stats=RepoStats(open_issues_count=42, open_prs_count=5, oldest_open_issue_age_days=180),
        interop=interop or InteropStatus(),
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


def test_render_stage_has_tooltip_with_description():
    html = render_index([_spec(stage="WD")])
    # The WD stage cell should carry a title attribute with the human-readable
    # description so hovering reveals what "WD" means.
    assert 'title="Working Draft' in html


def test_render_stage_tooltip_for_rec():
    html = render_index([_spec(stage="REC")])
    assert 'title="Recommendation' in html


def test_render_stage_tooltip_for_ed_with_no_tr():
    html = render_index([_spec(stage="ED", wpt_path=None)])
    assert 'title="Editor' in html  # "Editor's Draft — ..."


def test_render_open_issues_count_is_a_link():
    html = render_index([_spec("webcodecs")])
    assert 'href="https://github.com/w3c/webcodecs/issues"' in html


def test_render_open_prs_count_is_a_link():
    html = render_index([_spec("webcodecs")])
    assert 'href="https://github.com/w3c/webcodecs/pulls"' in html


def test_render_wpt_column_links_to_wpt_fyi_when_path_set():
    html = render_index([_spec("webcodecs", wpt_path="/webcodecs/")])
    assert "wpt.fyi/results/webcodecs" in html or "wpt.fyi/results//webcodecs" in html


def test_render_wpt_column_shows_dash_when_path_not_set():
    html = render_index([_spec("media-playback-quality", wpt_path=None)])
    # Don't link to wpt.fyi for this spec's row.
    # Use a structural assertion: no /results/ link for this spec.
    assert "wpt.fyi/results" not in html


def test_render_includes_wpt_link_for_spec_with_path():
    html = render_index([_spec()])
    assert "wpt.fyi" in html


def test_summarize_counts_specs_and_totals():
    from mediawg_dashboard.render import summarize

    specs = [_spec("a", "WD"), _spec("b", "REC"), _spec("c", "WD")]
    s = summarize(specs)
    assert s["total_specs"] == 3
    assert s["total_issues"] == 42 * 3
    assert s["total_prs"] == 5 * 3
    assert s["by_stage"] == {"WD": 2, "REC": 1}


def test_summarize_empty_list():
    from mediawg_dashboard.render import summarize

    s = summarize([])
    assert s == {
        "total_specs": 0,
        "total_issues": 0,
        "total_prs": 0,
        "by_stage": {},
        "shipping_cross_engine": 0,
    }


def test_summarize_counts_shipping_cross_engine():
    from mediawg_dashboard.render import summarize

    all_ship = _spec("a", interop=InteropStatus(chrome="shipped", firefox="shipped", safari="shipped"))
    partial = _spec("b", interop=InteropStatus(chrome="shipped", firefox="shipped", safari="partial"))
    s = summarize([all_ship, partial])
    assert s["shipping_cross_engine"] == 1


def test_render_shows_next_gate():
    html = render_index([_spec("webcodecs", stage="WD")])
    assert "→CR" in html


def test_render_shows_colored_interop_icons():
    html = render_index([
        _spec("webcodecs", interop=InteropStatus(chrome="shipped", firefox="none", safari="partial"))
    ])
    # Per-engine coloured support icons (green/red/amber via sup-* classes).
    assert "sup sup-shipped" in html
    assert "sup sup-none" in html
    assert "sup sup-partial" in html


def test_render_pulse_dash_without_health_data():
    # No health data -> no pulse mark is applied to a row (the "cell-value pulse-*"
    # wrapper only appears when a pulse is rendered; the CSS class defs don't count).
    html = render_index([_spec("webcodecs")])
    assert "cell-value pulse-" not in html


def test_render_summary_shows_shipping_count():
    html = render_index([
        _spec("a", interop=InteropStatus(chrome="shipped", firefox="shipped", safari="shipped"))
    ])
    assert "1 shipping cross-engine" in html


def test_render_rows_are_expandable():
    html = render_index([_spec("webcodecs")])
    assert 'class="spec-row"' in html
    assert 'class="panel-row"' in html
    assert 'id="panel-webcodecs"' in html
    # Panels start collapsed (hidden) — including in the narrow card layout.
    assert 'id="panel-webcodecs" hidden>' in html


def test_render_expand_affordance_is_discoverable():
    html = render_index([_spec("webcodecs")])
    # Keyboard-operable + a visible caret + a hint.
    assert 'tabindex="0"' in html and 'aria-expanded="false"' in html
    assert 'class="caret"' in html
    assert "click a row to expand" in html


def test_render_table_layout_fixed_keeps_columns_stable():
    # Fixed layout + colgroup so expanding a row can't re-flow the columns.
    html = render_index([_spec("webcodecs")])
    assert "table-layout: fixed" in html
    assert "<colgroup>" in html and 'class="col-interop"' in html


def test_render_cr_blocking_before_horizontal():
    # CR-blocking issues should render above Horizontal reviews in the checklist.
    html = render_index([_spec("webcodecs", stage="WD")])
    assert html.index("CR-blocking issues") < html.index("Horizontal reviews")


def test_render_panel_has_three_groups():
    html = render_index([_spec("webcodecs")])
    assert "Standardization" in html
    assert "Interoperability" in html
    assert "Activity" in html


def test_render_panel_lists_engines():
    html = render_index([_spec("webcodecs")])
    assert "Chromium" in html and "Firefox" in html and "Safari" in html


def test_render_charter_behind_tag_links_to_charter_when_overdue():
    from mediawg_dashboard.model import SpecHealth

    spec = _spec("webcodecs")
    spec.health = SpecHealth(charter_target="CR Q1 2026", charter_overdue=True)
    html = render_index([spec])
    assert "behind charter" in html
    assert "media-wg-charter.html#deliverables" in html
    assert "CR Q1 2026" in html  # in the tooltip


def test_render_no_charter_row_when_on_track():
    from mediawg_dashboard.model import SpecHealth

    spec = _spec("webcodecs")
    spec.health = SpecHealth(charter_target="CR Q1 2026", charter_overdue=False)
    html = render_index([spec])
    # On-track: no standalone charter clutter.
    assert "behind charter" not in html


def test_render_panel_shows_blocker_checklist():
    # A WD spec's next gate is CR; the panel lists its blocker labels.
    html = render_index([_spec("webcodecs", stage="WD")])
    assert "Wide review complete" in html
    assert "Horizontal reviews" in html


def test_render_summary_includes_totals():
    html = render_index([_spec("a", "WD"), _spec("b", "REC")])
    # Total open issues across two specs (42 + 42 = 84) should appear.
    assert ">84<" in html
    # Stage labels should appear in the summary strip.
    assert "WD" in html and "REC" in html


# --- Registries section ---


def test_render_no_registries_section_when_empty():
    # No registries → no second table (nothing to show).
    html = render_index([_spec()])
    assert 'id="registries"' not in html


def test_render_registries_section_appears():
    html = render_index([_spec()], registries=[_registry()])
    assert 'id="registries"' in html
    assert "registry track" in html
    assert "Webcodecs Codec Registry" in html


def test_render_registries_are_independent_table():
    # Two separate <table class="ledger"> with distinct ids so each sorts alone.
    html = render_index([_spec("webcodecs")], registries=[_registry()])
    assert 'id="specs"' in html
    assert 'id="registries"' in html
    # The generalized script wires every ledger, not just #specs.
    assert 'querySelectorAll("table.ledger")' in html
    assert 'getElementById("specs")' not in html


def test_render_registry_shows_stage_and_next_gate():
    html = render_index([_spec()], registries=[_registry(stage="Registry Draft")])
    assert "Registry Draft" in html
    # First level shows the short "→Snapshot"; the full name is in the panel/tooltip.
    assert "→Snapshot" in html
    assert "Candidate Snapshot" in html


def test_render_registry_shows_entry_count():
    html = render_index([_spec()], registries=[_registry(entry_count=13)])
    assert "13" in html


def test_render_registry_review_column():
    h = HorizontalReviews(a11y="resolved", i18n="open", privacy="open", security="open", tag="open")
    html = render_index([_spec()], registries=[_registry(horizontal=h)])
    assert "1/5" in html


def test_render_registry_panel_has_two_groups_no_interop():
    html = render_index([_spec()], registries=[_registry()])
    assert 'id="rpanel-webcodecs-codec-registry"' in html
    assert "panel-two" in html
    # A registry has no interop/WPT axis — the panel says so, and shows Entries.
    assert "isn&#39;t shipped or tested" in html or "isn't shipped or tested" in html


def test_render_registry_panel_starts_hidden():
    html = render_index([_spec()], registries=[_registry()])
    assert 'id="rpanel-webcodecs-codec-registry" hidden>' in html


def test_summarize_registries_counts_advanced():
    regs = [
        _registry("a", stage="Registry Draft"),
        _registry("b", stage="Candidate Snapshot"),
        _registry("c", stage="W3C Registry"),
    ]
    s = summarize_registries(regs)
    assert s["total"] == 3
    assert s["at_snapshot"] == 2  # Snapshot + W3C Registry


def test_summarize_registries_empty():
    assert summarize_registries([]) == {"total": 0, "at_snapshot": 0}
