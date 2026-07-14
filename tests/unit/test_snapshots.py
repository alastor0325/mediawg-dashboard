from mediawg_dashboard.snapshots import (
    issue_series,
    read_history,
    record_snapshot,
    write_history,
)


def test_record_and_series():
    h = {}
    record_snapshot(h, "2026-07-11", {"webcodecs": 210})
    record_snapshot(h, "2026-07-12", {"webcodecs": 214})
    assert issue_series(h, "webcodecs") == [210, 214]


def test_record_dedupes_same_day():
    h = {}
    record_snapshot(h, "2026-07-12", {"webcodecs": 210})
    record_snapshot(h, "2026-07-12", {"webcodecs": 214})  # same day replaces
    assert issue_series(h, "webcodecs") == [214]


def test_record_keeps_last_30():
    h = {}
    for i in range(35):
        record_snapshot(h, f"2026-06-{i:02d}", {"x": i})
    assert len(issue_series(h, "x")) == 30
    assert issue_series(h, "x")[-1] == 34


def test_issue_series_missing_spec():
    assert issue_series({}, "nope") == []


def test_read_write_roundtrip(tmp_path):
    path = tmp_path / "sub" / "history.json"
    assert read_history(path) == {}  # missing -> empty
    h = record_snapshot({}, "2026-07-12", {"a": 1})
    write_history(path, h)
    assert read_history(path) == {"a": [{"date": "2026-07-12", "open_issues": 1}]}
