from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from mediawg_dashboard.activity import ACTIVITY_WINDOW_DAYS
from mediawg_dashboard.analysis import registry_view, shipping_cross_engine, spec_view
from mediawg_dashboard.model import (
    REGISTRY_STAGE_DESCRIPTIONS,
    STAGE_DESCRIPTIONS,
    Registry,
    Spec,
)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"

WPT_FYI_BASE = "https://wpt.fyi/results"
# Source of the per-spec charter_target dates (the charter's deliverables table).
CHARTER_URL = "https://www.w3.org/2025/07/media-wg-charter.html#deliverables"


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _known_sum(values: list[int | None]) -> int | None:
    """Sum the known values; None if every spec's fetch failed (all unknown)."""
    known = [v for v in values if v is not None]
    return sum(known) if known else None


def summarize(specs: list[Spec]) -> dict:
    return {
        "total_specs": len(specs),
        "total_issues": _known_sum([s.stats.open_issues_count for s in specs]),
        "total_prs": _known_sum([s.stats.open_prs_count for s in specs]),
        "by_stage": dict(Counter(s.status.stage for s in specs)),
        "shipping_cross_engine": shipping_cross_engine(specs),
    }


def summarize_registries(registries: list[Registry]) -> dict:
    at_snapshot = sum(
        1 for r in registries if r.status.stage in ("Candidate Snapshot", "W3C Registry")
    )
    return {
        "total": len(registries),
        "at_snapshot": at_snapshot,  # advanced past Registry Draft
    }


def render_index(
    specs: list[Spec],
    refreshed_at: datetime | None = None,
    registries: list[Registry] | None = None,
) -> str:
    refreshed_at = refreshed_at or datetime.now(timezone.utc)
    registries = registries or []
    rows = [spec_view(spec, refreshed_at.date()) for spec in specs]
    registry_rows = [registry_view(reg, refreshed_at.date()) for reg in registries]
    template = _env().get_template("index.html.j2")
    return template.render(
        rows=rows,
        registry_rows=registry_rows,
        refreshed_iso=refreshed_at.strftime("%Y-%m-%d %H:%M UTC"),
        summary=summarize(specs),
        registry_summary=summarize_registries(registries),
        stage_descriptions=STAGE_DESCRIPTIONS,
        registry_stage_descriptions=REGISTRY_STAGE_DESCRIPTIONS,
        wpt_fyi_base=WPT_FYI_BASE,
        charter_url=CHARTER_URL,
        activity_window_days=ACTIVITY_WINDOW_DAYS,
    )
