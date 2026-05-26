from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from mediawg_dashboard.model import Spec

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_index(specs: list[Spec], refreshed_at: datetime | None = None) -> str:
    refreshed_at = refreshed_at or datetime.now(timezone.utc)
    template = _env().get_template("index.html.j2")
    return template.render(
        specs=specs,
        refreshed_at=refreshed_at.strftime("%Y-%m-%d %H:%M UTC"),
    )
