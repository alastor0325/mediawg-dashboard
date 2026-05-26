import os
import sys
from contextlib import nullcontext
from datetime import datetime, timezone

import httpx

from mediawg_dashboard.model import RepoStats

GITHUB_API_BASE = "https://api.github.com"

_MAX_PAGES = 20


def classify_issues_and_prs(items: list[dict]) -> tuple[list[dict], list[dict]]:
    issues: list[dict] = []
    prs: list[dict] = []
    for item in items:
        if "pull_request" in item:
            prs.append(item)
        else:
            issues.append(item)
    return issues, prs


def compute_oldest_issue_age_days(issues: list[dict], now: datetime | None = None) -> int | None:
    if not issues:
        return None
    now = now or datetime.now(timezone.utc)
    oldest = min(datetime.fromisoformat(i["created_at"]) for i in issues)
    return (now - oldest).days


def _auth_headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _fetch_all_pages(
    client: httpx.Client, url: str, params: dict[str, str | int]
) -> list[dict]:
    headers = _auth_headers()
    results: list[dict] = []
    response = client.get(url, params=params, headers=headers)
    response.raise_for_status()
    results.extend(response.json())
    next_url: str | None = response.links.get("next", {}).get("url")
    pages = 1
    while next_url and pages < _MAX_PAGES:
        # next_url already encodes all query parameters; passing params=None
        # preserves them. Passing params={} would strip them.
        response = client.get(next_url, headers=headers)
        response.raise_for_status()
        results.extend(response.json())
        next_url = response.links.get("next", {}).get("url")
        pages += 1
    if next_url:
        print(
            f"warning: {url} pagination truncated at _MAX_PAGES={_MAX_PAGES}; counts may be a floor",
            file=sys.stderr,
        )
    return results


def fetch_repo_stats(repo: str, client: httpx.Client | None = None) -> RepoStats:
    ctx = nullcontext(client) if client is not None else httpx.Client(follow_redirects=True, timeout=20.0)
    with ctx as c:
        items = _fetch_all_pages(
            c,
            f"{GITHUB_API_BASE}/repos/{repo}/issues",
            {"state": "open", "per_page": 100},
        )
    issues, prs = classify_issues_and_prs(items)
    return RepoStats(
        open_issues_count=len(issues),
        open_prs_count=len(prs),
        oldest_open_issue_age_days=compute_oldest_issue_age_days(issues),
    )
