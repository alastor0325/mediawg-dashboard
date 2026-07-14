from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from mediawg_dashboard.analysis import shipping_cross_engine, spec_view
from mediawg_dashboard.model import STAGE_DESCRIPTIONS, Spec

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"

WPT_FYI_BASE = "https://wpt.fyi/results"


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def summarize(specs: list[Spec]) -> dict:
    return {
        "total_specs": len(specs),
        "total_issues": sum(s.stats.open_issues_count for s in specs),
        "total_prs": sum(s.stats.open_prs_count for s in specs),
        "by_stage": dict(Counter(s.status.stage for s in specs)),
        "shipping_cross_engine": shipping_cross_engine(specs),
    }


def render_index(specs: list[Spec], refreshed_at: datetime | None = None) -> str:
    refreshed_at = refreshed_at or datetime.now(timezone.utc)
    rows = [spec_view(spec, refreshed_at.date()) for spec in specs]
    template = _env().get_template("index.html.j2")
    return template.render(
        rows=rows,
        refreshed_iso=refreshed_at.strftime("%Y-%m-%d %H:%M UTC"),
        summary=summarize(specs),
        stage_descriptions=STAGE_DESCRIPTIONS,
        wpt_fyi_base=WPT_FYI_BASE,
    )
