"""Horizontal-review status from the W3C horizontal groups' request repos.

The real, authoritative state of a spec's horizontal reviews lives in each
group's *request* repo (one issue per spec), NOT as ``*-tracker`` labels on the
spec's own repo (those are frequently empty). One cross-repo GitHub search per
spec fetches all five at once; the pure classifier maps each to a ReviewState.
"""

from contextlib import nullcontext

import httpx

from mediawg_dashboard.fetch.github import _auth_headers
from mediawg_dashboard.model import HorizontalReviews

GITHUB_API_BASE = "https://api.github.com"

# horizontal group -> the repo where its per-spec review requests are filed.
HR_REQUEST_REPOS: dict[str, str] = {
    "a11y": "w3c/a11y-request",
    "i18n": "w3c/i18n-request",
    "privacy": "w3cping/privacy-request",
    "security": "w3c/security-request",
    "tag": "w3ctag/design-reviews",
}
_GROUP_BY_REPO = {repo: group for group, repo in HR_REQUEST_REPOS.items()}


def hr_search_query(title: str) -> str:
    """A GitHub issue-search query: this spec's review issues across all 5 repos."""
    repos = " ".join(f"repo:{r}" for r in HR_REQUEST_REPOS.values())
    return f'"{title}" in:title is:issue {repos}'


def _repo_full_name(repository_url: str) -> str:
    """'https://api.github.com/repos/w3c/a11y-request' -> 'w3c/a11y-request'."""
    marker = "/repos/"
    idx = repository_url.find(marker)
    return repository_url[idx + len(marker):] if idx != -1 else ""


def _review_state(issue: dict) -> str:
    """A single request issue -> ReviewState.

    Closed = the review concluded (resolved); open = requested / in progress.
    """
    return "resolved" if issue.get("state") == "closed" else "requested"


def classify_reviews(items: list[dict]) -> HorizontalReviews:
    """Map cross-repo search results to the 5 horizontal-review states (pure).

    Buckets each issue by its repo's group, then for each group uses the
    most-recent issue (highest number) as the current status. A group with no
    matching issue stays ``unknown`` (we can't tell not-requested from a
    title mismatch).
    """
    by_group: dict[str, list[dict]] = {}
    for it in items:
        group = _GROUP_BY_REPO.get(_repo_full_name(it.get("repository_url", "")))
        if group is None or "pull_request" in it:
            continue
        by_group.setdefault(group, []).append(it)

    states: dict[str, str] = {}
    for group in HR_REQUEST_REPOS:
        issues = by_group.get(group)
        if not issues:
            states[group] = "unknown"
        else:
            latest = max(issues, key=lambda i: i.get("number", 0))
            states[group] = _review_state(latest)
    return HorizontalReviews(**states)


def fetch_horizontal_reviews(title: str, client: httpx.Client | None = None) -> HorizontalReviews:
    """Search the 5 request repos for ``title`` and classify each group's state."""
    ctx = nullcontext(client) if client is not None else httpx.Client(follow_redirects=True, timeout=20.0)
    with ctx as c:
        response = c.get(
            f"{GITHUB_API_BASE}/search/issues",
            params={"q": hr_search_query(title), "per_page": 100},
            headers=_auth_headers(),
        )
        response.raise_for_status()
        return classify_reviews(response.json().get("items", []))
