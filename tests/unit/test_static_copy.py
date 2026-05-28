from mediawg_dashboard.cli import copy_static


def test_copy_static_copies_files_preserving_layout(tmp_path):
    static = tmp_path / "static"
    output = tmp_path / "output"
    (static / "sub").mkdir(parents=True)
    (static / "favicon.svg").write_text("<svg/>")
    (static / "sub" / "icon.png").write_bytes(b"PNG")

    copied = copy_static(static, output)

    assert (output / "favicon.svg").read_text() == "<svg/>"
    assert (output / "sub" / "icon.png").read_bytes() == b"PNG"
    assert {p.name for p in copied} == {"favicon.svg", "icon.png"}


def test_copy_static_no_dir_returns_empty(tmp_path):
    assert copy_static(tmp_path / "does-not-exist", tmp_path / "output") == []


def test_copy_static_empty_dir_returns_empty(tmp_path):
    (tmp_path / "static").mkdir()
    assert copy_static(tmp_path / "static", tmp_path / "output") == []
