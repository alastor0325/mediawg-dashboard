import os
import sys
import time
from contextlib import nullcontext
from datetime import datetime, timezone

import httpx

from mediawg_dashboard.model import ActivityEvent, RepoStats

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


# --- Recent activity ("new this week") ---------------------------------------
#
# Pure extraction from the three raw payloads. Each comment counts as one event
# and each state change as one; the view dedupes them into per-thread rows.
#
# Not covered (and deliberately not fetched): **reopened** — invisible without a
# per-issue events call — and PR **review submissions** (approve / request
# changes), which need one call per PR. Both are documented limitations.


def thread_number(comment: dict) -> int | None:
    """The issue/PR number a comment belongs to (None if unparseable).

    Issue and PR-*conversation* comments carry ``issue_url``; PR **review**
    comments carry ``pull_request_url`` instead. Keying on only one of them
    silently drops a whole class of comments.
    """
    url = comment.get("issue_url") or comment.get("pull_request_url") or ""
    tail = url.rstrip("/").rsplit("/", 1)[-1]
    return int(tail) if tail.isdigit() else None


def build_thread_index(issues: list[dict]) -> dict[int, dict]:
    """Number → issues-listing entry, so a comment can resolve its thread's title."""
    return {i["number"]: i for i in issues if i.get("number") is not None}


def _thread_identity(issue: dict) -> tuple[str, str, str, str]:
    """(kind, title, url, state) for one issues-listing entry.

    A merged PR reports state "merged" rather than GitHub's "closed" — the
    distinction is what a reader actually wants from the row.
    """
    pull_request = issue.get("pull_request")
    kind = "pr" if pull_request is not None else "issue"
    state = issue.get("state") or ""
    if pull_request and pull_request.get("merged_at"):
        state = "merged"
    return kind, issue.get("title") or "", issue.get("html_url") or "", state


def _in_window(value: str | None, since: datetime) -> datetime | None:
    """Parsed timestamp if it falls in the window, else None."""
    if not value:
        return None
    at = _parse_iso(value)
    return at if at >= since else None


def _event(issue: dict, event: str, at: datetime, author: str | None) -> ActivityEvent:
    kind, title, url, state = _thread_identity(issue)
    return ActivityEvent(
        number=issue["number"], kind=kind, title=title, url=url,
        state=state, event=event, author=author, at=at,
    )


def extract_state_events(issues: list[dict], since: datetime) -> list[ActivityEvent]:
    """Opened / closed / merged events inside the window.

    A merged PR is also closed, so only "merged" is emitted for it — counting
    both would inflate the badge for every landed PR.
    """
    events: list[ActivityEvent] = []
    for issue in issues:
        if issue.get("number") is None:
            continue
        opened_at = _in_window(issue.get("created_at"), since)
        if opened_at:
            author = (issue.get("user") or {}).get("login")
            events.append(_event(issue, "opened", opened_at, author))
        # GitHub's payload names no actor for a close/merge, so author stays None.
        merged_at = _in_window((issue.get("pull_request") or {}).get("merged_at"), since)
        if merged_at:
            events.append(_event(issue, "merged", merged_at, None))
            continue
        closed_at = _in_window(issue.get("closed_at"), since)
        if closed_at:
            events.append(_event(issue, "closed", closed_at, None))
    return events


def extract_comment_events(
    comments: list[dict], index: dict[int, dict], since: datetime
) -> list[ActivityEvent]:
    """One event per comment in the window, titled from ``index``.

    A comment whose thread isn't in the index is skipped — without a title there
    is no honest row to show, and skipping keeps the badge equal to the sum of
    the listed threads. Only reachable when the issues listing hit the
    ``_MAX_PAGES`` cap, which already warns on its own.
    """
    events: list[ActivityEvent] = []
    for comment in comments:
        number = thread_number(comment)
        issue = index.get(number) if number is not None else None
        if issue is None:
            continue
        at = _in_window(comment.get("created_at"), since)
        if at is None:
            continue
        events.append(_event(issue, "comment", at, (comment.get("user") or {}).get("login")))
    return events


def _iso_z(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _fetch_since(
    repo: str,
    path: str,
    since: datetime,
    client: httpx.Client | None,
    extra: dict[str, str] | None = None,
) -> list[dict]:
    """Paginated GET of a repo sub-resource filtered by ``since`` (shared by the
    three activity fetchers)."""
    params: dict[str, str | int] = {"since": _iso_z(since), "per_page": 100}
    params.update(extra or {})
    with _client_ctx(client) as c:
        return _fetch_all_pages(c, f"{GITHUB_API_BASE}/repos/{repo}/{path}", params)


def fetch_updated_issues(
    repo: str, since: datetime, client: httpx.Client | None = None
) -> list[dict]:
    """Issues+PRs touched since ``since`` — the source of titles and state changes.

    ``state=all`` is required: the default (open) would drop everything closed or
    merged during the window, which is exactly the activity worth reporting.
    """
    return _fetch_since(
        repo, "issues", since, client, {"state": "all", "sort": "updated", "direction": "desc"}
    )


def fetch_issue_comments(
    repo: str, since: datetime, client: httpx.Client | None = None
) -> list[dict]:
    """Repo-wide comments on issues and PR conversations since ``since``."""
    return _fetch_since(repo, "issues/comments", since, client)


def fetch_review_comments(
    repo: str, since: datetime, client: httpx.Client | None = None
) -> list[dict]:
    """Repo-wide inline PR *review* comments since ``since``."""
    return _fetch_since(repo, "pulls/comments", since, client)


def _auth_headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _client_ctx(client: httpx.Client | None):
    """Reuse the caller's client, or own a short-lived one (shared by the fetchers)."""
    if client is not None:
        return nullcontext(client)
    return httpx.Client(follow_redirects=True, timeout=20.0)


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
    with _client_ctx(client) as c:
        return _fetch_all_pages(
            c,
            f"{GITHUB_API_BASE}/repos/{repo}/issues",
            {"state": "open", "per_page": 100},
        )


def fetch_recent_commits(
    repo: str, client: httpx.Client | None = None, per_page: int = 100
) -> list[dict]:
    """Most recent commits on the default branch (for activity + author signals)."""
    with _client_ctx(client) as c:
        response = github_get(
            c,
            f"{GITHUB_API_BASE}/repos/{repo}/commits",
            params={"per_page": per_page},
        )
        return response.json()
