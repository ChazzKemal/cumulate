"""One way in, whatever the file is.

    from ingest import profile, load, describe

    profile(path)   -> dict describing the file, uniform across types
    load(path)      -> the data (DataFrame for tables, dict/list for json, str for text)
    describe(path)  -> the same profile as plain text, ready to show someone

Spreadsheets, CSV, JSON/JSONL/YAML, and text/logs are handled. For anything else,
write a reader in scaffold/readers/ — see that package's docstring.
"""
from __future__ import annotations

from pathlib import Path

from readers import reader_for, supported

__all__ = ["profile", "load", "describe", "list_sheets", "supported", "UnsupportedFile"]


class UnsupportedFile(Exception):
    """No reader for this file type yet. Write one in scaffold/readers/."""


def _reader(path: str | Path):
    r = reader_for(path)
    if r is None:
        raise UnsupportedFile(
            f"No reader for '{Path(path).suffix}'. Supported: {', '.join(supported())}. "
            f"Write one in scaffold/readers/ and it will be picked up automatically."
        )
    return r


def profile(path: str | Path) -> dict:
    return _reader(path).profile(path)


def load(path: str | Path, **kw):
    return _reader(path).load(path, **kw)


def list_sheets(path: str | Path) -> list[str]:
    r = _reader(path)
    return r.list_sheets(path) if hasattr(r, "list_sheets") else []


def describe(path: str | Path) -> str:
    """The profile as prose — what you read out to someone before asking questions."""
    p = profile(path)
    lines = [f"{p['file']} — {p.get('kind', 'unknown')}"]

    if "sheets" in p:
        for name, s in p["sheets"].items():
            lines.append(f"\n  Sheet '{name}': {s['rows']:,} rows × {len(s['columns'])} columns")
            lines.append(f"    Columns: {', '.join(map(str, s['columns']))}")
            for w in s.get("warnings", []):
                lines.append(f"    ⚠ {w}")
    else:
        for k in ("records", "lines", "keys", "levels"):
            if k in p:
                v = p[k]
                lines.append(f"  {k}: {', '.join(map(str, v)) if isinstance(v, list) else v}")
        for w in p.get("warnings", []):
            lines.append(f"  ⚠ {w}")

    return "\n".join(lines)
