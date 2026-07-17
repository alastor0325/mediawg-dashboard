"""Persist the last-known-good page state so a fetch outage falls back to the
previous values instead of showing unknown.

Stores the fully-assembled Spec/Registry objects (keyed by shortname) as JSON,
rewritten every refresh. Reads are defensive: a missing or corrupt file, or an
entry that no longer validates against the current model, is simply skipped.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from pydantic import ValidationError

from mediawg_dashboard.model import Registry, Spec


def load_last_good(path: Path) -> tuple[dict[str, Spec], dict[str, Registry]]:
    """Return ({shortname: Spec}, {shortname: Registry}) from the store (empty
    dicts if the file is absent/unreadable)."""
    if not path.exists():
        return {}, {}
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        print(f"warning: could not read {path}: {exc}", file=sys.stderr)
        return {}, {}

    specs: dict[str, Spec] = {}
    for key, raw in (data.get("specs") or {}).items():
        try:
            specs[key] = Spec.model_validate(raw)
        except ValidationError:
            pass  # stale schema — ignore this entry
    registries: dict[str, Registry] = {}
    for key, raw in (data.get("registries") or {}).items():
        try:
            registries[key] = Registry.model_validate(raw)
        except ValidationError:
            pass
    return specs, registries


def save_last_good(path: Path, specs: list[Spec], registries: list[Registry]) -> None:
    """Overwrite the store with the current (already merged) page state."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "specs": {s.meta.shortname: s.model_dump(mode="json") for s in specs},
        "registries": {r.meta.shortname: r.model_dump(mode="json") for r in registries},
    }
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False))
