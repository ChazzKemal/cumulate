"""Source files somebody wrote before this existed.

Not run, not imported, not judged — read. An old script is a written-down
decision, and the parts worth reading are rarely the clever ones: the constant
at the top, the number in the middle of a condition, the branch that exists
because of one customer.

So the profile points at those. Definitions to say what it is made of, literal
assignments and bare thresholds because that is where a domain rule hides, and
the TODO nobody got to because it is usually the honest bit.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

EXTENSIONS = (".py", ".r", ".sql", ".vba", ".bas", ".cls", ".js", ".ts",
              ".sh", ".ps1", ".m", ".ipynb")

LANGUAGES = {
    ".py": "Python", ".r": "R", ".sql": "SQL", ".vba": "VBA", ".bas": "VBA",
    ".cls": "VBA", ".js": "JavaScript", ".ts": "TypeScript", ".sh": "Shell",
    ".ps1": "PowerShell", ".m": "MATLAB/Octave", ".ipynb": "Jupyter notebook",
}

# Run them all regardless of language. A stray match in a profile costs nothing;
# a missed procedure means someone reads the whole file by hand.
DEFINITIONS = (
    re.compile(r"^\s*(?:async\s+)?def\s+(\w+)", re.M),
    re.compile(r"^\s*class\s+(\w+)", re.M),
    re.compile(r"^\s*(\w+)\s*(?:<-|=)\s*function\s*\(", re.M),
    re.compile(r"^\s*(?:Public\s+|Private\s+)?(?:Sub|Function)\s+(\w+)", re.M | re.I),
    re.compile(r"^\s*(?:export\s+)?function\s+(\w+)", re.M),
    re.compile(r"^\s*CREATE\s+(?:OR\s+REPLACE\s+)?(?:PROCEDURE|PROC|FUNCTION|VIEW)\s+"
               r"[\[\"`]?([\w.]+)", re.M | re.I),
    re.compile(r"^\s*(\w+)\s*\(\s*\)\s*\{", re.M),
)

# NAME = 0.175  /  rate <- 42  /  Const VAT As Double = 0.2  /  @cap = 1000
ASSIGNED = re.compile(
    r"^\s*(?:Const\s+|const\s+|let\s+|var\s+|final\s+|SET\s+)?@?(\w{2,})"
    r"(?:\s+As\s+\w+)?\s*(?:<-|=|:=)\s*"
    r"(-?\d+\.?\d*(?:e-?\d+)?|'[^'\n]{1,60}'|\"[^\"\n]{1,60}\")\s*(?:;|$|#|'|//)",
    re.M | re.I)

# A number sitting inside a comparison is a threshold somebody chose.
THRESHOLD = re.compile(r"[<>]=?\s*(-?\d+\.\d+|-?\d{2,})")

FLAGGED = re.compile(r"(?:#|//|--|')\s*(TODO|FIXME|HACK|XXX|NOTE|BUG|WORKAROUND)\b[:\s]*(.{0,120})",
                     re.I)

COMMENT_ONLY = re.compile(r"^\s*(?:#|//|--|'|/\*|\*)")


def load(path: str | Path, **_) -> str:
    """The source. Notebooks come back as their code cells, joined."""
    path = Path(path)
    text = path.read_text(errors="replace")
    if path.suffix.lower() != ".ipynb":
        return text
    try:
        nb = json.loads(text)
    except json.JSONDecodeError:
        return text
    cells = []
    for cell in nb.get("cells", []):
        src = cell.get("source", "")
        src = "".join(src) if isinstance(src, list) else src
        if cell.get("cell_type") == "code":
            cells.append(src)
        elif src.strip():
            cells.append("\n".join(f"# {l}" for l in src.splitlines()))
    return "\n\n".join(cells)


def profile(path: str | Path) -> dict:
    path = Path(path)
    src = load(path)
    lines = src.splitlines()
    code = [l for l in lines if l.strip() and not COMMENT_ONLY.match(l)]

    defined: list[str] = []
    for pat in DEFINITIONS:
        for name in pat.findall(src):
            if name not in defined:
                defined.append(name)

    constants = {}
    for name, value in ASSIGNED.findall(src):
        if name.lower() in {"i", "j", "n", "x", "y", "df", "self"}:
            continue
        constants.setdefault(name, value.strip())

    thresholds = []
    for m in THRESHOLD.findall(src):
        if m not in thresholds:
            thresholds.append(m)

    out = {
        "file": path.name,
        "kind": "code",
        "language": LANGUAGES.get(path.suffix.lower(), "source"),
        "lines": len(lines),
        "code_lines": len(code),
        "defines": defined[:40],
        "constants": dict(list(constants.items())[:30]),
        "thresholds": thresholds[:20],
        "flagged": [f"{tag.upper()}: {note.strip()}" for tag, note in FLAGGED.findall(src)][:15],
        "sample": lines[:15],
        "warnings": [],
    }

    if constants:
        out["warnings"].append(
            f"{len(constants)} hardcoded value{'s' if len(constants) != 1 else ''} "
            "— each one is a decision somebody made")
    if thresholds:
        out["warnings"].append(
            f"{len(thresholds)} number{'s' if len(thresholds) != 1 else ''} compared against "
            "in a condition — ask what they mean before reusing them")
    if out["flagged"]:
        out["warnings"].append(f"{len(out['flagged'])} TODO/FIXME left in the source")
    if not defined and len(code) > 40:
        out["warnings"].append("no functions — reads as a top-to-bottom script")

    return out
