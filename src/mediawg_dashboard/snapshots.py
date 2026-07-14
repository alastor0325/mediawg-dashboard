"""Daily snapshot history for trend signals (e.g. backlog rising/falling).

Pure dict helpers (``record_snapshot``, ``issue_series``) are unit-tested;
``read_history``/``write_history`` are the only I/O.
"""

import json
from pathlib import Path

_MAX_ENTRIES = 30


def read_history(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def write_history(path: Path, history: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, indent=0, sort_keys=True))


def record_snapshot(history: dict, day: str, open_issue_counts: dict[str, int]) -> dict:
    """Append today's open-issue count per spec, de-duping same-day, keeping last N."""
    for name, count in open_issue_counts.items():
        entries = [e for e in history.get(name, []) if e.get("date") != day]
        entries.append({"date": day, "open_issues": count})
        history[name] = entries[-_MAX_ENTRIES:]
    return history


def issue_series(history: dict, name: str) -> list[int]:
    """Open-issue counts for a spec, oldest→newest."""
    return [e["open_issues"] for e in history.get(name, [])]
