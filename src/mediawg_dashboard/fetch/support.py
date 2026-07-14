"""Browser-support fetch + pure mapping (via webstatus.dev).

The pure parser (``parse_support``) is unit-tested; the thin fetch needs a
per-spec ``webstatus_id`` (config) and live validation. When no id is set the
caller keeps support 'unknown' — honest degradation, never a guess.
"""

from contextlib import nullcontext

import httpx

from mediawg_dashboard.model import InteropStatus, SupportState

WEBSTATUS_API_BASE = "https://api.webstatus.dev/v1"

# webstatus.dev implementation status -> our neutral SupportState.
_STATUS_MAP: dict[str, SupportState] = {
    "available": "shipped",
    "unavailable": "none",
}


def parse_support(payload: dict) -> InteropStatus:
    """Map a webstatus.dev feature payload to per-engine SupportState.

    Expects ``{"browser_implementations": {"chrome": {"status": "available"},
    "firefox": {...}, "safari": {...}}}``. Missing engines stay 'unknown'.
    Only interop identity (per-engine status) is set here; WPT numbers come from
    the wpt fetch.
    """
    impls = payload.get("browser_implementations") or {}

    def state(engine: str) -> SupportState:
        entry = impls.get(engine) or {}
        return _STATUS_MAP.get(entry.get("status", ""), "unknown")

    return InteropStatus(
        chrome=state("chrome"),
        firefox=state("firefox"),
        safari=state("safari"),
    )


def fetch_support(webstatus_id: str | None, client: httpx.Client | None = None) -> InteropStatus:
    """Fetch per-engine support for a feature id (unknown InteropStatus if no id)."""
    if not webstatus_id:
        return InteropStatus()
    ctx = nullcontext(client) if client is not None else httpx.Client(follow_redirects=True, timeout=20.0)
    with ctx as c:
        resp = c.get(f"{WEBSTATUS_API_BASE}/features/{webstatus_id}")
        if resp.status_code == 404:
            return InteropStatus()
        resp.raise_for_status()
        return parse_support(resp.json())
