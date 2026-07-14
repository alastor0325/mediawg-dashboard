"""Browser-support from MDN browser-compat-data (BCD).

Source is the always-current BCD on the MDN GitHub main branch. A spec maps to
one representative BCD feature (``bcd_path`` in config, e.g. ``api.MediaSource``).
The pure parser (``parse_bcd_support``) is unit-tested; the thin fetch loads the
one relevant BCD file and degrades to 'unknown' on any error.
"""

from contextlib import nullcontext

import httpx

from mediawg_dashboard.model import InteropStatus, SupportState

BCD_RAW = "https://raw.githubusercontent.com/mdn/browser-compat-data/main"


def bcd_file_url(bcd_path: str) -> str:
    """The BCD JSON file that contains ``bcd_path`` (category/interface.json)."""
    parts = bcd_path.split(".")
    return f"{BCD_RAW}/{parts[0]}/{parts[1]}.json"


def _engine_state(entry) -> tuple[SupportState, str | None]:
    """Map one BCD browser support entry to (SupportState, version|None)."""
    if entry is None:
        return ("unknown", None)
    if isinstance(entry, list):  # multiple ranges — the first is current
        entry = entry[0]
    version = entry.get("version_added")
    if version is False:
        return ("none", None)
    if version is None:
        return ("unknown", None)
    if version == "preview":
        return ("partial", None)  # nightly/preview only
    if entry.get("partial_implementation") or entry.get("flags"):
        v = version.lstrip("≤") if isinstance(version, str) else None
        return ("partial", v)
    if version is True:
        return ("shipped", None)
    if isinstance(version, str):
        return ("shipped", version.lstrip("≤"))
    return ("unknown", None)


def parse_bcd_support(data: dict, bcd_path: str) -> InteropStatus:
    """Extract per-engine support + versions + MDN url for ``bcd_path``."""
    node = data
    for segment in bcd_path.split("."):
        node = node[segment]
    compat = node["__compat"]
    support = compat.get("support", {})
    cs, cv = _engine_state(support.get("chrome"))
    fs, fv = _engine_state(support.get("firefox"))
    ss, sv = _engine_state(support.get("safari"))
    return InteropStatus(
        chrome=cs, firefox=fs, safari=ss,
        chrome_version=cv, firefox_version=fv, safari_version=sv,
        mdn_url=compat.get("mdn_url"),
    )


def fetch_support(bcd_path: str | None, client: httpx.Client | None = None) -> InteropStatus:
    """Fetch per-engine support for a BCD feature (unknown InteropStatus if no path)."""
    if not bcd_path:
        return InteropStatus()
    ctx = nullcontext(client) if client is not None else httpx.Client(follow_redirects=True, timeout=20.0)
    with ctx as c:
        resp = c.get(bcd_file_url(bcd_path))
        if resp.status_code == 404:
            return InteropStatus()
        resp.raise_for_status()
        return parse_bcd_support(resp.json(), bcd_path)
