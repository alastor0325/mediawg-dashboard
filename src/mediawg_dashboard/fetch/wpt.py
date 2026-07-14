"""wpt.fyi fetch + pure scoring.

The pure parser (``parse_wpt_scores``) is fully unit-tested against the
documented wpt.fyi ``/api/search`` shape; the thin fetch wires the two API
calls (latest stable runs -> results) and needs live validation on first run.
"""

from contextlib import nullcontext

import httpx

WPT_API_BASE = "https://wpt.fyi/api"

# The engines we report, in neutral alphabetical order.
ENGINES = ("chrome", "firefox", "safari")


def parse_wpt_scores(payload: dict) -> dict:
    """Aggregate a wpt.fyi search payload into neutral interop numbers.

    Expects ``{"runs": [{"browser_name": ...}, ...], "results": [{"test": ...,
    "legacy_status": [{"passes": int, "total": int}, ...]}, ...]}`` where each
    result's ``legacy_status`` aligns with ``runs`` by index.

    Returns ``{"all_engines_wpt": float|None, "wpt_test_count": int,
    "per_engine": {engine: pct}}`` where ``all_engines_wpt`` is the share of
    tests that pass fully in *every* run (the honest "works everywhere" figure).
    """
    runs = payload.get("runs", [])
    results = payload.get("results", [])
    order = [r.get("browser_name", "") for r in runs]

    totals = {b: [0, 0] for b in order}  # engine -> [passes, total]
    all_pass = 0
    for res in results:
        status = res.get("legacy_status") or []
        test_passes_everywhere = bool(order) and len(status) == len(order)
        for i, engine in enumerate(order):
            if i >= len(status):
                test_passes_everywhere = False
                continue
            passes = status[i].get("passes", 0)
            total = status[i].get("total", 0)
            totals[engine][0] += passes
            totals[engine][1] += total
            if not (total > 0 and passes == total):
                test_passes_everywhere = False
        if test_passes_everywhere:
            all_pass += 1

    test_count = len(results)
    all_engines_wpt = round(all_pass / test_count * 100, 1) if test_count else None
    per_engine = {b: (p, t) for b, (p, t) in totals.items()}  # (passes, total)
    return {
        "all_engines_wpt": all_engines_wpt,
        "wpt_test_count": test_count,
        "per_engine": per_engine,
    }


def fetch_experimental_run_ids(client: httpx.Client) -> list[str]:
    """Latest *aligned* experimental (nightly) run ids for the three engines.

    Aligned = same revision across engines, so the pass rates are comparable.
    Spec-independent, so fetch once per refresh.
    """
    products = ",".join(f"{e}[experimental]" for e in ENGINES)
    resp = client.get(
        f"{WPT_API_BASE}/runs",
        params={"products": products, "aligned": "true", "max-count": 1},
    )
    resp.raise_for_status()
    return [str(run["id"]) for run in resp.json()]


def fetch_wpt_scores(
    wpt_path: str, run_ids: list[str], client: httpx.Client | None = None
) -> dict | None:
    """Score ``wpt_path`` against pre-fetched stable ``run_ids`` (None if no runs)."""
    if not run_ids:
        return None
    ctx = nullcontext(client) if client is not None else httpx.Client(follow_redirects=True, timeout=30.0)
    with ctx as c:
        # wpt.fyi search matches the path as a plain substring (no 'path:' op).
        resp = c.get(
            f"{WPT_API_BASE}/search",
            params={"run_ids": ",".join(run_ids), "q": wpt_path},
        )
        resp.raise_for_status()
        return parse_wpt_scores(resp.json())
