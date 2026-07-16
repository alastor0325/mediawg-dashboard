from contextlib import nullcontext
from datetime import date

import httpx

from mediawg_dashboard.model import RegistryStage, RegistryStatus, SpecStatus, Stage

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


def _fetch_latest_version(w3c_shortname, client, on_404, parse):
    """Fetch a spec/registry's latest /TR/ version, degrading to ``on_404``.

    Shared by the spec and registry fetchers — they differ only in the 404
    fallback and how the payload is parsed.
    """
    url = f"{W3C_API_BASE}/specifications/{w3c_shortname}/versions/latest"
    ctx = nullcontext(client) if client is not None else httpx.Client(follow_redirects=True, timeout=15.0)
    with ctx as c:
        response = c.get(url)
        if response.status_code == 404:
            return on_404
        response.raise_for_status()
        return parse(response.json())


def fetch_spec_status(w3c_shortname: str, client: httpx.Client | None = None) -> SpecStatus:
    # 404 = no /TR/ publication yet (Editor's Draft only).
    return _fetch_latest_version(
        w3c_shortname, client, SpecStatus(stage="ED", last_tr_publication=None, ed_url=None), parse_spec_version
    )


# W3C API registry-track status strings → our RegistryStage (verified: the API
# returns "Draft Registry" for the current Registry Draft stage).
_REGISTRY_STATUS_MAP: dict[str, RegistryStage] = {
    "Draft Registry": "Registry Draft",
    "Registry Draft": "Registry Draft",
    "Candidate Registry": "Candidate Snapshot",
    "Candidate Registry Snapshot": "Candidate Snapshot",
    "Registry": "W3C Registry",
    "W3C Registry": "W3C Registry",
}


def parse_registry_version(payload: dict) -> RegistryStatus:
    stage: RegistryStage = _REGISTRY_STATUS_MAP.get(payload.get("status", ""), "unknown")
    date_str = payload.get("date")
    last_published = date.fromisoformat(date_str) if date_str else None
    return RegistryStatus(stage=stage, last_published=last_published)


def fetch_registry_status(w3c_shortname: str, client: httpx.Client | None = None) -> RegistryStatus:
    return _fetch_latest_version(
        w3c_shortname, client, RegistryStatus(stage="unknown", last_published=None), parse_registry_version
    )
