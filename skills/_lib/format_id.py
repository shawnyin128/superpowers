"""Centralized id-to-display rendering for sp-harness skills.

Reads `.claude/features.json` and `.claude/todos.json` and exposes:
- get_display_name(id, kind) -> str — raw display_name lookup
- format_id(id, kind) -> str — wraps as "<id>(<display_name>)"

All errors are loud. There is no fallback to bare id when display_name is
missing or empty — that case is a schema invariant violation and signals
an upstream bug. The whole point of this module is to make such silent
drift impossible.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

VALID_KINDS = ("feature", "todo")
_KIND_TO_FILE = {
    "feature": ("features.json", "features"),
    "todo": ("todos.json", "todos"),
}


def _find_claude_dir(start: Path | None = None) -> Path:
    """Walk up from `start` (default cwd) to find a `.claude/` directory."""
    cur = (start or Path.cwd()).resolve()
    for candidate in (cur, *cur.parents):
        target = candidate / ".claude"
        if target.is_dir():
            return target
    raise FileNotFoundError(
        f".claude/ not found walking up from {cur}"
    )


def _load_entries(kind: str) -> Iterable[dict]:
    if kind not in _KIND_TO_FILE:
        raise ValueError(
            f"invalid kind {kind!r}; must be one of {VALID_KINDS}"
        )
    filename, list_key = _KIND_TO_FILE[kind]
    path = _find_claude_dir() / filename
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get(list_key, [])


def get_display_name(id: str, kind: str) -> str:
    """Return the display_name for `id` in features.json or todos.json.

    Raises ValueError on unknown id, missing/empty display_name, or
    invalid kind. Raises FileNotFoundError if the source file or the
    enclosing .claude/ directory cannot be found.
    """
    entries = _load_entries(kind)
    for entry in entries:
        if entry.get("id") == id:
            name = entry.get("display_name")
            if not isinstance(name, str) or not name.strip():
                raise ValueError(
                    f"{kind} {id!r}: display_name is missing or empty "
                    f"(schema invariant violated)"
                )
            return name
    raise ValueError(f"{kind} id {id!r} not found")


def format_id(id: str, kind: str) -> str:
    """Return the universal "<id>(<display_name>)" rendering."""
    return f"{id}({get_display_name(id, kind)})"
