"""Pure URL builders for the detail panel (GitHub filters, wpt.fyi, webstatus)."""

from urllib.parse import quote

GITHUB = "https://github.com"
WPT_FYI = "https://wpt.fyi/results"
# Cross-group per-spec horizontal-review view (all 5 groups for one spec).
HR_TRACKER = "https://w3c.github.io/horizontal-issue-tracker/review.html"

# The horizontal-review groups and the label suffixes W3C uses.
_HGROUPS = ("a11y", "i18n", "privacy", "security", "tag")

# The horizontal groups' *request* repos — where each spec's review is actually
# filed (and where the review state is read from). Single source of truth,
# imported by fetch/horizontal.py.
HR_REQUEST_REPOS: dict[str, str] = {
    "a11y": "w3c/a11y-request",
    "i18n": "w3c/i18n-request",
    "privacy": "w3cping/privacy-request",
    "security": "w3c/security-request",
    "tag": "w3ctag/design-reviews",
}


def issues_search_url(repo: str, query: str) -> str:
    """A GitHub issue-search URL for ``repo`` with a raw search ``query``."""
    return f"{GITHUB}/{repo}/issues?q={quote(query)}"


def repo_issues_url(repo: str) -> str:
    """The repo's open issues — the venue for broad (wide) review discussion."""
    return f"{GITHUB}/{repo}/issues"


def needs_resolution_url(repo: str) -> str:
    """Open issues carrying any ``*-needs-resolution`` label (the blocking ones)."""
    labels = ",".join(f"{g}-needs-resolution" for g in _HGROUPS)
    return issues_search_url(repo, f"is:open is:issue label:{labels}")


def horizontal_request_url(group: str, query: str) -> str | None:
    """Fallback link for a horizontal-review chip: the group's request repo
    filtered to this spec (used when the exact review issue URL isn't known)."""
    repo = HR_REQUEST_REPOS.get(group)
    if not repo:
        return None
    return issues_search_url(repo, f'"{query}" in:title is:issue')


def hr_review_url(hr_shortname: str) -> str:
    """The horizontal-issue-tracker's cross-group review page for one spec."""
    return f"{HR_TRACKER}?shortname={quote(hr_shortname)}"


def wpt_url(wpt_path: str | None) -> str | None:
    return f"{WPT_FYI}{wpt_path}" if wpt_path else None
