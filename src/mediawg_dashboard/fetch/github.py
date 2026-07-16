import os
import sys
import time
from contextlib import nullcontext
from datetime import datetime, timezone

import httpx

from mediawg_dashboard.model import RepoStats

GITHUB_API_BASE = "https://api.github.com"

_MAX_PAGES = 20
_RETRY_STATUSES = {429, 500, 502, 503, 504}


def github_get(
    client: httpx.Client, url: str, params=None, headers=None, retries: int = 2, backoff: float = 1.5
) -> httpx.Response:
    """GET with a short retry on transient GitHub errors (429 / 5xx), so a brief
    outage doesn't zero the whole refresh. Raises on the final failure."""
    headers = headers if headers is not None else _auth_headers()
    for attempt in range(retries + 1):
        response = client.get(url, params=params, headers=headers)
        if response.status_code in _RETRY_STATUSES and attempt < retries:
            time.sleep(backoff * (attempt + 1))
            continue
        response.raise_for_status()
        return response
    return response  # unreachable; keeps type-checkers happy


def _parse_iso(value: str) -> datetime:
    """Parse a GitHub ISO timestamp, tolerating a trailing 'Z'."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


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
    oldest = min(_parse_iso(i["created_at"]) for i in issues)
    return (now - oldest).days


def compute_repo_stats(items: list[dict], now: datetime | None = None) -> RepoStats:
    """Build RepoStats from a raw open-issues+PRs list (single source of truth)."""
    issues, prs = classify_issues_and_prs(items)
    return RepoStats(
        open_issues_count=len(issues),
        open_prs_count=len(prs),
        oldest_open_issue_age_days=compute_oldest_issue_age_days(issues, now=now),
    )


def _label_names(issue: dict) -> set[str]:
    return {label["name"] for label in issue.get("labels", [])}


def count_labeled(issues: list[dict], label: str) -> int:
    return sum(1 for i in issues if label in _label_names(i))


def needs_resolution_stats(
    issues: list[dict], now: datetime | None = None
) -> tuple[int, int | None]:
    """Count of open ``*-needs-resolution`` issues and the oldest one's age (days)."""
    now = now or datetime.now(timezone.utc)
    dated = [
        _parse_iso(i["created_at"])
        for i in issues
        if any(name.endswith("-needs-resolution") for name in _label_names(i))
    ]
    if not dated:
        return (0, None)
    return (len(dated), (now - min(dated)).days)


def days_since_last_commit(commits: list[dict], now: datetime | None = None) -> int | None:
    """Days since the most recent commit (None if no commits)."""
    if not commits:
        return None
    now = now or datetime.now(timezone.utc)
    latest = max(_parse_iso(c["commit"]["author"]["date"]) for c in commits)
    return (now - latest).days


def monthly_commit_counts(
    commits: list[dict], now: datetime | None = None, months: int = 6
) -> list[tuple[str, int]]:
    """Commit counts per calendar month for the last ``months`` (oldest→newest).

    Returns ``[("2026-02", 5), …]`` — the data behind the activity sparkline.
    (Bounded by the fetched commit window; very busy repos may undercount the
    oldest buckets.)
    """
    now = now or datetime.now(timezone.utc)
    buckets: list[tuple[int, int]] = []
    y, m = now.year, now.month
    for _ in range(months):
        buckets.append((y, m))
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    buckets.reverse()
    index = {ym: i for i, ym in enumerate(buckets)}
    counts = [0] * months
    for c in commits:
        d = _parse_iso(c["commit"]["author"]["date"])
        i = index.get((d.year, d.month))
        if i is not None:
            counts[i] += 1
    return [(f"{y:04d}-{m:02d}", counts[i]) for i, (y, m) in enumerate(buckets)]


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
    response = github_get(client, url, params=params, headers=headers)
    results.extend(response.json())
    next_url: str | None = response.links.get("next", {}).get("url")
    pages = 1
    while next_url and pages < _MAX_PAGES:
        # next_url already encodes all query parameters; passing params=None
        # preserves them. Passing params={} would strip them.
        response = github_get(client, next_url, headers=headers)
        results.extend(response.json())
        next_url = response.links.get("next", {}).get("url")
        pages += 1
    if next_url:
        print(
            f"warning: {url} pagination truncated at _MAX_PAGES={_MAX_PAGES}; counts may be a floor",
            file=sys.stderr,
        )
    return results


def fetch_open_issues(repo: str, client: httpx.Client | None = None) -> list[dict]:
    """Raw open issues+PRs for a repo (feeds both stats and the label parsers)."""
    ctx = nullcontext(client) if client is not None else httpx.Client(follow_redirects=True, timeout=20.0)
    with ctx as c:
        return _fetch_all_pages(
            c,
            f"{GITHUB_API_BASE}/repos/{repo}/issues",
            {"state": "open", "per_page": 100},
        )


def fetch_recent_commits(
    repo: str, client: httpx.Client | None = None, per_page: int = 100
) -> list[dict]:
    """Most recent commits on the default branch (for activity + author signals)."""
    ctx = nullcontext(client) if client is not None else httpx.Client(follow_redirects=True, timeout=20.0)
    with ctx as c:
        response = github_get(
            c,
            f"{GITHUB_API_BASE}/repos/{repo}/commits",
            params={"per_page": per_page},
        )
        return response.json()
