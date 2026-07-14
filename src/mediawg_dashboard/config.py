from pathlib import Path

import yaml

from mediawg_dashboard.model import SpecMeta


def load_specs(path: Path) -> list[SpecMeta]:
    data = yaml.safe_load(path.read_text())
    return [
        SpecMeta(
            shortname=entry["shortname"],
            title=entry["title"],
            repo=entry["repo"],
            w3c_shortname=entry.get("w3c_shortname") or entry["shortname"],
            tr_url=entry.get("tr"),
            wpt_path=entry.get("wpt_path"),
            charter_target=entry.get("charter_target"),
            webstatus_id=entry.get("webstatus_id"),
        )
        for entry in data["specs"]
    ]
