from pathlib import Path

from mediawg_dashboard.config import load_specs

REPO_CONFIG = Path(__file__).resolve().parents[2] / "config" / "specs.yaml"

SAMPLE_YAML = """
specs:
  - shortname: webcodecs
    title: WebCodecs
    repo: w3c/webcodecs
    tr: https://www.w3.org/TR/webcodecs/
    charter_target: CR Q1 2026
    webstatus_id: webcodecs
  - shortname: autoplay
    title: Autoplay Policy Detection
    repo: w3c/autoplay
    w3c_shortname: autoplay-detection
    tr: https://www.w3.org/TR/autoplay-detection/
"""


def test_load_specs_returns_list_of_meta(tmp_path):
    cfg = tmp_path / "specs.yaml"
    cfg.write_text(SAMPLE_YAML)
    specs = load_specs(cfg)
    assert len(specs) == 2
    assert specs[0].shortname == "webcodecs"
    assert specs[1].w3c_shortname == "autoplay-detection"


def test_load_specs_w3c_shortname_defaults_to_shortname(tmp_path):
    cfg = tmp_path / "specs.yaml"
    cfg.write_text(SAMPLE_YAML)
    specs = load_specs(cfg)
    assert specs[0].w3c_shortname == "webcodecs"


def test_repo_specs_yaml_parses():
    # Regression: the shipped config must load (a stray line once broke refresh).
    specs = load_specs(REPO_CONFIG)
    assert len(specs) == 9
    assert all(s.shortname and s.repo for s in specs)


def test_load_specs_parses_charter_and_webstatus(tmp_path):
    cfg = tmp_path / "specs.yaml"
    cfg.write_text(SAMPLE_YAML)
    specs = load_specs(cfg)
    assert specs[0].charter_target == "CR Q1 2026"
    assert specs[0].webstatus_id == "webcodecs"
    # Absent fields default to None.
    assert specs[1].charter_target is None
    assert specs[1].webstatus_id is None
