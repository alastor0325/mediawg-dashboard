from contextlib import nullcontext
from datetime import date

import httpx

from mediawg_dashboard.model import SpecStatus, Stage

W3C_API_BASE = "https://api.w3.org"

_STATUS_MAP: dict[str, Stage] = {
    "Working Draft": "WD",
    "First Public Working Draft": "FPWD",
    "Candidate Recommendation": "CR",
    "Candidate Recommendation Snapshot": "CR-snapshot",
    "Candidate Recommendation Draft": "CR-draft",
    "Proposed Recommendation": "PR",
    "Recommendation": "REC",
    "Group Note": "NOTE",
    "Note": "NOTE",
    "Working Group Note": "NOTE",
    "Discontinued Draft": "Discontinued",
    "Retired Recommendation": "Discontinued",
}


def parse_spec_version(payload: dict) -> SpecStatus:
    stage: Stage = _STATUS_MAP.get(payload.get("status", ""), "unknown")
    date_str = payload.get("date")
    last_tr = date.fromisoformat(date_str) if date_str else None
    ed_url = payload.get("editor-draft") or None
    return SpecStatus(stage=stage, last_tr_publication=last_tr, ed_url=ed_url)


def fetch_spec_status(w3c_shortname: str, client: httpx.Client | None = None) -> SpecStatus:
    url = f"{W3C_API_BASE}/specifications/{w3c_shortname}/versions/latest"
    ctx = nullcontext(client) if client is not None else httpx.Client(follow_redirects=True, timeout=15.0)
    with ctx as c:
        response = c.get(url)
        if response.status_code == 404:
            # Spec has no /TR/ publication yet (Editor's Draft only).
            return SpecStatus(stage="ED", last_tr_publication=None, ed_url=None)
        response.raise_for_status()
        return parse_spec_version(response.json())
