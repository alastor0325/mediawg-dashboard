from datetime import date

from mediawg_dashboard.fetch.w3c import parse_spec_version


def test_parse_working_draft():
    payload = {
        "status": "Working Draft",
        "date": "2026-05-05",
        "editor-draft": "https://w3c.github.io/webcodecs/",
        "uri": "https://www.w3.org/TR/2026/WD-webcodecs-20260505/",
    }
    status = parse_spec_version(payload)
    assert status.stage == "WD"
    assert status.last_tr_publication == date(2026, 5, 5)
    assert status.ed_url == "https://w3c.github.io/webcodecs/"


def test_parse_recommendation():
    payload = {
        "status": "Recommendation",
        "date": "2017-09-18",
        "editor-draft": "https://w3c.github.io/encrypted-media/",
        "uri": "https://www.w3.org/TR/2017/REC-encrypted-media-20170918/",
    }
    assert parse_spec_version(payload).stage == "REC"


def test_parse_cr_snapshot():
    payload = {"status": "Candidate Recommendation Snapshot", "date": "2024-09-01"}
    assert parse_spec_version(payload).stage == "CR-snapshot"


def test_parse_cr_draft():
    payload = {"status": "Candidate Recommendation Draft", "date": "2024-10-01"}
    assert parse_spec_version(payload).stage == "CR-draft"


def test_parse_proposed_recommendation():
    payload = {"status": "Proposed Recommendation", "date": "2024-01-01"}
    assert parse_spec_version(payload).stage == "PR"


def test_parse_group_note():
    payload = {"status": "Group Note", "date": "2024-01-01"}
    assert parse_spec_version(payload).stage == "NOTE"


def test_parse_unknown_status_falls_back_to_unknown():
    payload = {"status": "Some Future Status We Don't Know", "date": "2024-01-01"}
    assert parse_spec_version(payload).stage == "unknown"


def test_parse_missing_date_is_none():
    payload = {"status": "Working Draft"}
    assert parse_spec_version(payload).last_tr_publication is None


def test_parse_missing_ed_url_is_none():
    payload = {"status": "Working Draft", "date": "2024-01-01"}
    assert parse_spec_version(payload).ed_url is None
