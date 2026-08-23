"""Plain text, logs, markdown. Profiled by shape, not parsed."""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

EXTENSIONS = (".txt", ".log", ".md", ".out", ".err")


def load(path: str | Path, **_) -> str:
    return Path(path).read_text(errors="replace")


def profile(path: str | Path) -> dict:
    path = Path(path)
    lines = load(path).splitlines()
    out = {
        "file": path.name,
        "kind": "text",
        "lines": len(lines),
        "sample": lines[:10],
        "warnings": [],
    }
    ts = re.compile(r"^\s*(\d{4}-\d{2}-\d{2}|\d{2}:\d{2}:\d{2})")
    head = lines[:100]
    if head and sum(bool(ts.match(l)) for l in head) / len(head) > 0.5:
        out["kind"] = "log"
        levels = Counter(m.group(1) for l in lines
                         if (m := re.search(r"\b(ERROR|WARN|WARNING|INFO|DEBUG|FATAL)\b", l)))
        if levels:
            out["levels"] = dict(levels)
            if levels.get("ERROR", 0) or levels.get("FATAL", 0):
                out["warnings"].append(f"{levels.get('ERROR',0)+levels.get('FATAL',0)} error lines")
    return out
