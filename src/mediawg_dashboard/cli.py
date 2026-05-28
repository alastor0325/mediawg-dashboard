import shutil
import sys
import time
from pathlib import Path

import httpx

from mediawg_dashboard.config import load_specs
from mediawg_dashboard.fetch.github import fetch_repo_stats
from mediawg_dashboard.fetch.w3c import fetch_spec_status
from mediawg_dashboard.model import Spec, SpecMeta
from mediawg_dashboard.render import render_index

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "specs.yaml"
STATIC_DIR = REPO_ROOT / "static"
OUTPUT_PATH = REPO_ROOT / "output" / "index.html"


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


def _fetch_one(meta: SpecMeta, client: httpx.Client) -> Spec:
    status = fetch_spec_status(meta.w3c_shortname, client=client)
    stats = fetch_repo_stats(meta.repo, client=client)
    return Spec(meta=meta, status=status, stats=stats)


def cmd_refresh() -> int:
    metas = load_specs(CONFIG_PATH)
    specs: list[Spec] = []
    with httpx.Client(follow_redirects=True, timeout=20.0) as client:
        for meta in metas:
            t0 = time.time()
            print(f"  fetching {meta.shortname}…", end="", flush=True, file=sys.stderr)
            specs.append(_fetch_one(meta, client))
            print(f" {time.time()-t0:.1f}s", file=sys.stderr)
    html = render_index(specs)
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
