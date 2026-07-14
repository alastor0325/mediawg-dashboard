"""Pure URL builders for the detail panel (GitHub filters, wpt.fyi, webstatus)."""

from urllib.parse import quote

GITHUB = "https://github.com"
WPT_FYI = "https://wpt.fyi/results"
WEBSTATUS = "https://webstatus.dev/features"

# The horizontal-review groups and the label suffixes W3C uses.
_HGROUPS = ("a11y", "i18n", "privacy", "security", "tag")


def issues_search_url(repo: str, query: str) -> str:
    """A GitHub issue-search URL for ``repo`` with a raw search ``query``."""
    return f"{GITHUB}/{repo}/issues?q={quote(query)}"


def needs_resolution_url(repo: str) -> str:
    """Open issues carrying any ``*-needs-resolution`` label (the blocking ones)."""
    labels = ",".join(f"{g}-needs-resolution" for g in _HGROUPS)
    return issues_search_url(repo, f"is:open is:issue label:{labels}")


def horizontal_group_url(repo: str, group: str) -> str:
    """Open issues for one horizontal group (tracker + needs-resolution)."""
    return issues_search_url(repo, f"is:open is:issue label:{group}-needs-resolution,{group}-tracker")


def webstatus_url(webstatus_id: str | None) -> str | None:
    return f"{WEBSTATUS}/{webstatus_id}" if webstatus_id else None


def wpt_url(wpt_path: str | None) -> str | None:
    return f"{WPT_FYI}{wpt_path}" if wpt_path else None
