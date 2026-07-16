from pathlib import Path

import yaml

from mediawg_dashboard.model import RegistryEntry, RegistryMeta, SpecMeta


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
            bcd_path=entry.get("bcd_path"),
            hr_shortname=entry.get("hr_shortname"),
            hr_query=entry.get("hr_query"),
            published_rec=entry.get("published_rec"),
        )
        for entry in data["specs"]
    ]


def load_registries(path: Path) -> list[RegistryMeta]:
    """Load the registry-track entries (empty if the file has no ``registries:``)."""
    data = yaml.safe_load(path.read_text())
    return [
        RegistryMeta(
            shortname=entry["shortname"],
            title=entry["title"],
            parent=entry["parent"],
            repo=entry["repo"],
            w3c_shortname=entry.get("w3c_shortname") or entry["shortname"],
            tr_url=entry.get("tr"),
            hr_shortname=entry.get("hr_shortname"),
            hr_query=entry.get("hr_query"),
            entries=[RegistryEntry(**e) for e in (entry.get("entries") or [])],
        )
        for entry in (data.get("registries") or [])
    ]
