"""Registry-track (Process §6.5) unit tests: config, W3C parse, assemble, analysis."""

from datetime import date
from pathlib import Path

from mediawg_dashboard.analysis import (
    compute_registry_blockers,
    registry_gate_readiness,
    registry_next_gate,
    registry_view,
)
from mediawg_dashboard.assemble import build_registry
from mediawg_dashboard.config import load_registries
from mediawg_dashboard.fetch.w3c import parse_registry_version
from mediawg_dashboard.model import (
    HorizontalReviews,
    Registry,
    RegistryEntry,
    RegistryMeta,
    RegistryStatus,
    SpecMilestones,
)

REPO_CONFIG = Path(__file__).resolve().parents[2] / "config" / "specs.yaml"

TODAY = date(2026, 7, 16)


def _registry(stage="Registry Draft", horizontal=None, entries=None, last_published=None):
    if entries is None:
        entries = [RegistryEntry(value="opus", note="Opus")]
    return Registry(
        meta=RegistryMeta(
            shortname="webcodecs-codec-registry",
            title="WebCodecs Codec",
            parent="WebCodecs",
            repo="w3c/webcodecs",
            w3c_shortname="webcodecs-codec-registry",
            tr_url="https://www.w3.org/TR/webcodecs-codec-registry/",
            entries=entries,
        ),
        status=RegistryStatus(stage=stage, last_published=last_published),
        milestones=SpecMilestones(horizontal=horizontal or HorizontalReviews()),
    )


# --- next-gate model ---


def test_registry_next_gate_draft_to_snapshot():
    assert registry_next_gate("Registry Draft") == "Candidate Snapshot"


def test_registry_next_gate_snapshot_to_registry():
    assert registry_next_gate("Candidate Snapshot") == "W3C Registry"


def test_registry_next_gate_terminal():
    assert registry_next_gate("W3C Registry") is None
    assert registry_next_gate("unknown") is None


# --- blockers / readiness ---


def test_draft_blockers_are_horizontal_only():
    # The Draft→Snapshot gate is tracked via the horizontal reviews — no broad
    # "wide review" blocker.
    blockers = compute_registry_blockers("Registry Draft", SpecMilestones())
    kinds = [b.kind for b in blockers]
    assert kinds == ["horizontal"]


def test_snapshot_gate_needs_ac_review():
    blockers = compute_registry_blockers("Candidate Snapshot", SpecMilestones())
    assert [b.kind for b in blockers] == ["ac_review"]


def test_terminal_registry_has_no_blockers():
    assert compute_registry_blockers("W3C Registry", SpecMilestones()) == []


def test_readiness_not_ready_when_reviews_unknown():
    # Fresh Registry Draft: horizontal reviews unknown → not ready.
    assert registry_gate_readiness("Registry Draft", SpecMilestones()) != "ready"


def test_readiness_ready_when_all_reviews_resolved():
    m = SpecMilestones(
        horizontal=HorizontalReviews(
            a11y="resolved", i18n="resolved", privacy="resolved", security="resolved", tag="resolved"
        ),
    )
    assert registry_gate_readiness("Registry Draft", m) == "ready"


def test_readiness_blocked_with_open_review():
    m = SpecMilestones(horizontal=HorizontalReviews(security="open"))
    assert registry_gate_readiness("Registry Draft", m) == "blocked"


# --- registry_view ---


def test_registry_view_review_label_counts_resolved():
    h = HorizontalReviews(a11y="resolved", i18n="resolved", privacy="open", security="open", tag="open")
    view = registry_view(_registry(horizontal=h), TODAY)
    assert view.review_label == "2/5"
    assert view.review_state == "partial"
    assert view.review_glyph == "◐"


def test_registry_view_next_gate_and_readiness():
    entries = [RegistryEntry(value=v) for v in ("a", "b", "c")]
    view = registry_view(_registry(entries=entries), TODAY)
    # entries are read off registry.meta in the template, not copied to the view.
    assert len(view.registry.meta.entries) == 3
    assert view.next_gate == "Candidate Snapshot"
    assert view.readiness in ("blocked", "unknown")


def test_registry_view_stage_age_from_last_published():
    view = registry_view(_registry(last_published=date(2026, 7, 6)), TODAY)
    assert view.stage_age_days == 10


def test_registry_view_horizontal_rows_link_to_request_repos():
    view = registry_view(_registry(), TODAY)
    assert len(view.horizontal_rows) == 5
    names = [name for name, _, _ in view.horizontal_rows]
    assert names == ["a11y", "i18n", "privacy", "security", "TAG"]
    # With no known issue URL, chips fall back to each group's request repo.
    hrefs = [href for _, _, href in view.horizontal_rows]
    assert "w3c/a11y-request/issues" in hrefs[0]
    assert "w3ctag/design-reviews/issues" in hrefs[4]


def test_registry_view_terminal_has_no_next_gate():
    view = registry_view(_registry(stage="W3C Registry"), TODAY)
    assert view.next_gate is None
    assert view.readiness is None
    assert view.blocker_rows == []


# --- W3C API parsing ---


def test_parse_registry_draft_status():
    # The W3C API returns "Draft Registry" for the Registry Draft stage.
    status = parse_registry_version({"status": "Draft Registry", "date": "2026-06-04"})
    assert status.stage == "Registry Draft"
    assert status.last_published == date(2026, 6, 4)


def test_parse_candidate_registry_status():
    assert parse_registry_version({"status": "Candidate Registry"}).stage == "Candidate Snapshot"


def test_parse_final_registry_status():
    assert parse_registry_version({"status": "Registry"}).stage == "W3C Registry"


def test_parse_unknown_registry_status():
    assert parse_registry_version({"status": "Mystery"}).stage == "unknown"


# --- assemble ---


def test_build_registry_carries_horizontal_and_status():
    meta = RegistryMeta(
        shortname="eme-hdcp-version-registry",
        title="EME HDCP Version",
        parent="EME",
        repo="w3c/encrypted-media",
        w3c_shortname="eme-hdcp-version-registry",
    )
    hz = HorizontalReviews(security="resolved", i18n="requested")
    reg = build_registry(meta, RegistryStatus(stage="Registry Draft"), hz)
    assert reg.milestones.horizontal.security == "resolved"
    assert reg.milestones.horizontal.i18n == "requested"
    assert reg.status.stage == "Registry Draft"
    # AC review can't be derived from public sources.
    assert reg.milestones.ac_review_done is None


def test_build_registry_horizontal_defaults_unknown():
    meta = RegistryMeta(shortname="r", title="R", parent="P", repo="w3c/r", w3c_shortname="r")
    reg = build_registry(meta, RegistryStatus(stage="unknown"))
    assert reg.milestones.horizontal.a11y == "unknown"


# --- config ---


def test_load_registries_from_sample(tmp_path):
    cfg = tmp_path / "specs.yaml"
    cfg.write_text(
        """
specs: []
registries:
  - shortname: eme-hdcp-version-registry
    title: EME HDCP Version
    parent: EME
    repo: w3c/encrypted-media
    tr: https://www.w3.org/TR/eme-hdcp-version-registry/
    entries:
      - { value: "1.0" }
      - { value: "2.3", note: "latest" }
"""
    )
    regs = load_registries(cfg)
    assert len(regs) == 1
    assert regs[0].parent == "EME"
    assert len(regs[0].entries) == 2
    assert regs[0].entries[0].value == "1.0"
    assert regs[0].entries[1].note == "latest"
    assert regs[0].w3c_shortname == "eme-hdcp-version-registry"  # defaults to shortname


def test_load_registries_absent_section_is_empty(tmp_path):
    cfg = tmp_path / "specs.yaml"
    cfg.write_text("specs: []\n")
    assert load_registries(cfg) == []


def test_repo_config_has_six_registries():
    # Regression: the shipped config's 6 registry-track deliverables must load.
    regs = load_registries(REPO_CONFIG)
    assert len(regs) == 6
    assert all(r.shortname and r.repo and r.parent for r in regs)
    assert all(r.entries for r in regs)  # every registry lists its registered values
    # Verified counts (2026-07-16): codec registry has 13 entries.
    codec = next(r for r in regs if r.shortname == "webcodecs-codec-registry")
    assert len(codec.entries) == 13
    assert any(e.group == "Video" for e in codec.entries)
