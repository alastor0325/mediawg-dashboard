from datetime import date

from mediawg_dashboard.laststate import load_last_good, save_last_good
from mediawg_dashboard.model import (
    InteropStatus,
    Registry,
    RegistryMeta,
    RegistryStatus,
    RepoStats,
    Spec,
    SpecMeta,
    SpecStatus,
)


def _spec(shortname="webcodecs", issues=140) -> Spec:
    return Spec(
        meta=SpecMeta(shortname=shortname, title=shortname.title(), repo=f"w3c/{shortname}", w3c_shortname=shortname),
        status=SpecStatus(stage="WD", last_tr_publication=date(2026, 5, 5)),
        stats=RepoStats(open_issues_count=issues, open_prs_count=9),
        interop=InteropStatus(chrome="shipped"),
    )


def _registry(shortname="webcodecs-codec-registry") -> Registry:
    return Registry(
        meta=RegistryMeta(shortname=shortname, title="X", parent="P", repo="w3c/x", w3c_shortname=shortname),
        status=RegistryStatus(stage="Registry Draft"),
    )


def test_round_trips_specs_and_registries(tmp_path):
    path = tmp_path / "last_good.json"
    save_last_good(path, [_spec("webcodecs", 140), _spec("autoplay", 14)], [_registry()])
    specs, registries = load_last_good(path)
    assert set(specs) == {"webcodecs", "autoplay"}
    assert specs["webcodecs"].stats.open_issues_count == 140
    assert specs["autoplay"].status.stage == "WD"
    assert registries["webcodecs-codec-registry"].status.stage == "Registry Draft"


def test_missing_file_returns_empty(tmp_path):
    specs, registries = load_last_good(tmp_path / "nope.json")
    assert specs == {} and registries == {}


def test_corrupt_file_returns_empty(tmp_path):
    path = tmp_path / "last_good.json"
    path.write_text("{ not json")
    assert load_last_good(path) == ({}, {})


def test_stale_schema_entry_is_skipped(tmp_path):
    path = tmp_path / "last_good.json"
    path.write_text('{"specs": {"x": {"garbage": true}}, "registries": {}}')
    specs, registries = load_last_good(path)
    assert specs == {} and registries == {}  # invalid entry dropped, no crash
