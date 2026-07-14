import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, TypeVar

import httpx

from mediawg_dashboard.analysis import trend_direction
from mediawg_dashboard.assemble import build_spec
from mediawg_dashboard.config import load_specs
from mediawg_dashboard.fetch.github import fetch_open_issues, fetch_recent_commits
from mediawg_dashboard.fetch.support import fetch_support
from mediawg_dashboard.fetch.w3c import fetch_spec_status
from mediawg_dashboard.fetch.wpt import fetch_experimental_run_ids, fetch_wpt_scores
from mediawg_dashboard.model import InteropStatus, Spec, SpecMeta, SpecStatus
from mediawg_dashboard.render import render_index
from mediawg_dashboard.snapshots import issue_series, read_history, record_snapshot, write_history

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "specs.yaml"
STATIC_DIR = REPO_ROOT / "static"
OUTPUT_PATH = REPO_ROOT / "output" / "index.html"
HISTORY_PATH = REPO_ROOT / "data" / "history.json"

T = TypeVar("T")


def copy_static(static_dir: Path, output_dir: Path) -> list[Path]:
    copied: list[Path] = []
    if not static_dir.is_dir():
        return copied
    for src in static_dir.rglob("*"):
        if not src.is_file():
            continue
        dst = output_dir / src.relative_to(static_dir)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(dst)
    return copied


def _safe(label: str, fn: Callable[[], T], default: T) -> T:
    """Run a fetch, degrading to a default on any error so one bad API or repo
    doesn't sink the whole refresh (the UI already renders 'unknown' cleanly)."""
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 — fetch failures must not abort refresh
        print(f" [warn: {label} failed: {exc}]", end="", file=sys.stderr)
        return default


def _fetch_one(
    meta: SpecMeta, client: httpx.Client, now: datetime, run_ids: list[str]
) -> tuple[Spec, bool]:
    """Fetch + assemble one spec. Second tuple element = whether the issues fetch
    succeeded (so a degraded fetch isn't recorded as a real backlog of 0)."""
    status = _safe("w3c", lambda: fetch_spec_status(meta.w3c_shortname, client=client), SpecStatus(stage="unknown"))
    raw_issues = _safe("issues", lambda: fetch_open_issues(meta.repo, client=client), None)
    commits = _safe("commits", lambda: fetch_recent_commits(meta.repo, client=client), [])
    wpt = _safe("wpt", lambda: fetch_wpt_scores(meta.wpt_path, run_ids, client=client), None) if meta.wpt_path else None
    support = _safe("support", lambda: fetch_support(meta.bcd_path, client=client), InteropStatus())
    spec = build_spec(meta, status, raw_issues or [], commits, wpt, support, now)
    return spec, raw_issues is not None


def cmd_refresh() -> int:
    metas = load_specs(CONFIG_PATH)
    now = datetime.now(timezone.utc)
    specs: list[Spec] = []
    ok_counts: dict[str, int] = {}
    with httpx.Client(follow_redirects=True, timeout=30.0) as client:
        run_ids = _safe("wpt-runs", lambda: fetch_experimental_run_ids(client), [])
        for meta in metas:
            t0 = time.time()
            print(f"  fetching {meta.shortname}…", end="", flush=True, file=sys.stderr)
            spec, issues_ok = _fetch_one(meta, client, now, run_ids)
            specs.append(spec)
            if issues_ok:
                ok_counts[meta.shortname] = spec.stats.open_issues_count
            print(f" {time.time()-t0:.1f}s", file=sys.stderr)

    # Record today's snapshot (only for specs whose issue fetch succeeded, so a
    # fetch outage never looks like a backlog crash) and derive the trend.
    history = read_history(HISTORY_PATH)
    record_snapshot(history, now.date().isoformat(), ok_counts)
    for spec in specs:
        series = issue_series(history, spec.meta.shortname)
        # Only surface a trend once there are ≥2 daily points; otherwise it's
        # a meaningless "flat".
        spec.health.backlog_trend = trend_direction(series) if len(series) >= 2 else None
    write_history(HISTORY_PATH, history)

    html = render_index(specs, now)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html)
    static_copied = copy_static(STATIC_DIR, OUTPUT_PATH.parent)
    print(f"wrote {OUTPUT_PATH} ({len(specs)} specs, {len(static_copied)} static files)")
    return 0


def cmd_brief() -> int:
    print("brief: not yet implemented")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("usage: python -m mediawg_dashboard.cli {refresh|brief}", file=sys.stderr)
        return 1
    command = args[0]
    if command == "refresh":
        return cmd_refresh()
    if command == "brief":
        return cmd_brief()
    print(f"unknown command: {command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
