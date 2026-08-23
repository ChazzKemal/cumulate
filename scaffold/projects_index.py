"""What was built before this existed. Hardcoded — no model involved.

The sibling of tools_index.py. That one lists what this workspace has made;
this one lists what came in from outside — old spreadsheets, scripts, reports
somebody maintained by hand. Read straight from the folder. Run it to print
the list.

projects/ is git-ignored, so glob and file search cannot see into it. That is
the whole reason this exists: the launcher runs it and hands the names over,
so the agent knows the work already happened instead of starting from nothing.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import workspace  # noqa: E402

ROOT = workspace()
PROJECTS = ROOT / "projects"

NOTE_NAMES = ("notes.txt", "notes.md", "readme.md", "readme.txt", "about.txt")

# Plain words, because the person reading this does not think in file extensions.
KINDS = {
    ".xlsx": "spreadsheet", ".xlsm": "spreadsheet", ".xls": "spreadsheet",
    ".csv": "table", ".tsv": "table",
    ".json": "data", ".jsonl": "data", ".yaml": "data", ".yml": "data",
    ".xml": "data", ".parquet": "data", ".db": "database", ".sqlite": "database",
    ".accdb": "database", ".mdb": "database",
    ".py": "code", ".r": "code", ".sql": "code", ".vba": "code", ".bas": "code",
    ".js": "code", ".ts": "code", ".m": "code", ".sh": "code", ".ps1": "code",
    ".ipynb": "notebook",
    ".docx": "document", ".pdf": "document", ".pptx": "document",
    ".txt": "notes", ".md": "notes", ".log": "log",
}

SKIP_DIRS = {"__pycache__", ".git", ".ipynb_checkpoints", "node_modules", ".venv"}


def _note(folder: Path) -> str:
    """First real line of whatever note they left. Blank if they left none."""
    for name in NOTE_NAMES:
        f = folder / name
        if not f.exists():
            continue
        for line in f.read_text(errors="replace").splitlines():
            line = line.strip().lstrip("#").strip()
            if line:
                return line
    return ""


def _files(folder: Path) -> list[Path]:
    return [f for f in sorted(folder.rglob("*"))
            if f.is_file()
            and not f.name.startswith(".")
            and not any(p in SKIP_DIRS for p in f.relative_to(folder).parts)]


def _entry(name: str, files: list[Path], note: str, root: Path) -> dict:
    kinds = []
    for f in files:
        k = KINDS.get(f.suffix.lower(), "file")
        if k not in kinds:
            kinds.append(k)
    newest = max((f.stat().st_mtime for f in files), default=0)
    return {
        "slug": name,
        "note": note,
        "files": len(files),
        "kinds": kinds,
        "names": [f.name for f in files],
        "updated": datetime.fromtimestamp(newest).strftime("%Y-%m-%d") if newest else "",
        "path": str(root.relative_to(ROOT)),
    }


def index() -> list[dict]:
    if not PROJECTS.exists():
        return []
    found = []
    for d in sorted(PROJECTS.iterdir()):
        if d.name.startswith(".") or d.name in SKIP_DIRS:
            continue
        if d.is_dir():
            files = _files(d)
            if files:
                found.append(_entry(d.name, files, _note(d), d))
        # A single file dropped straight in counts as a project of its own —
        # people will do that, and refusing to see it helps nobody.
        elif d.name.lower() != "readme.md":
            found.append(_entry(d.stem, [d], "", d))
    return found


def as_lines() -> str:
    """For a person to read."""
    projects = index()
    if not projects:
        return "  Nothing yet — drop old work into the projects folder."
    out = []
    for p in projects:
        what = p["note"] or f"{p['files']} file{'s' if p['files'] != 1 else ''}"
        out.append(f"  {p['slug']} — {what}  [{', '.join(p['kinds'])}, {p['updated']}]")
    return "\n".join(out)


def as_prompt() -> str:
    """For the agent. Terse on purpose, and explicit about what not to do."""
    projects = index()
    if not projects:
        return ""
    bits = "; ".join(
        f"{p['path']} ({p['note'] or ', '.join(p['kinds'])}: {', '.join(p['names'][:6])}"
        f"{'…' if len(p['names']) > 6 else ''})"
        for p in projects)
    return (f"Previous work already sitting in projects/: {bits}. "
            "This folder is gitignored, so glob and file search will not find it — "
            "read by path. If what I ask for overlaps one of these, say so and offer "
            "to read the old one before you build anything; the rules are usually "
            "buried in it. Do not open any of it until I have asked for something.")


if __name__ == "__main__":
    print(as_prompt() if "--prompt" in sys.argv else as_lines())
