"""What tools already exist. Hardcoded — no model involved.

Read straight from the files: the Streamlit title and caption every tool already
declares, plus how many assumptions it records. Run it to print the list.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import workspace  # noqa: E402

ROOT = workspace()
TOOLS = ROOT / "tools"


def _grab(src: str, fn: str) -> str:
    """Match the closing quote to the opening one — captions contain apostrophes."""
    m = re.search(rf'st\.{fn}\(\s*(["\'])(.+?)\1', src, re.S)
    return m.group(2).strip() if m else ""


def index() -> list[dict]:
    if not TOOLS.exists():
        return []
    found = []
    for d in sorted(TOOLS.iterdir()):
        app = d / "app.py"
        if not d.is_dir() or not app.exists():
            continue
        src = app.read_text(errors="replace")
        assumptions = d / "ASSUMPTIONS.md"
        n = 0
        if assumptions.exists():
            n = sum(1 for l in assumptions.read_text().splitlines()
                    if l.strip().startswith("- "))
        found.append({
            "slug": d.name,
            "name": _grab(src, "title") or d.name,
            "what": _grab(src, "caption"),
            "assumptions": n,
            "updated": datetime.fromtimestamp(app.stat().st_mtime).strftime("%Y-%m-%d"),
            "path": str(app.relative_to(ROOT)),
        })
    return found


def as_lines() -> str:
    """One line per tool, for a person to read."""
    tools = index()
    if not tools:
        return "No tools built yet."
    return "\n".join(
        f"  {t['name']} ({t['slug']}) — {t['what'] or 'no description'}"
        f"  [{t['assumptions']} assumptions, updated {t['updated']}]"
        for t in tools)


def as_prompt() -> str:
    """One line, for the agent. Kept terse on purpose."""
    tools = index()
    if not tools:
        return "No tools exist yet in tools/."
    bits = "; ".join(f"{t['slug']} ({t['what'] or t['name']})" for t in tools)
    return (f"Tools that already exist in tools/: {bits}. "
            "If what I want is one of these, open it and adapt it rather than "
            "building a second copy — and say so first.")


if __name__ == "__main__":
    print(as_prompt() if "--prompt" in sys.argv else as_lines())
