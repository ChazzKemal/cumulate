"""Install the capture trigger into Codex's hooks. Idempotent.

Python rather than shell so it runs on Windows too, and so the hook it installs
needs no shell either — the old version wired in `sh -c ...`, which simply never
fired on a Windows machine.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import os

# The hook lives with the code; it is installed into the person's workspace.
APP = Path(os.environ.get("CUMULATE_APP") or Path(__file__).resolve().parent.parent)
ROOT = Path(os.environ.get("CUMULATE_WORKSPACE") or APP)


def main() -> int:
    f = ROOT / ".codex" / "hooks.json"
    if not f.exists():
        print("Session recording isn't set up yet.")
        return 1

    cfg = json.loads(f.read_text())
    hook = APP / "hooks" / "on_session_end.py"
    events = cfg.setdefault("hooks", {})

    # SessionEnd is the normal trigger. SessionStart is the safety net: if a
    # session was killed hard and SessionEnd never fired, the next one sweeps
    # up whatever was missed.
    added = []
    for event in ("SessionEnd", "SessionStart"):
        arg = "end" if event == "SessionEnd" else "start"
        command = f'"{sys.executable}" "{hook}" {arg}'
        group = events.setdefault(event, [{"matcher": None, "hooks": []}])
        if any("on_session_end" in h.get("command", "") or "on-session-end" in h.get("command", "")
               for g in group for h in g.get("hooks", [])):
            continue
        group[0].setdefault("hooks", []).append(
            {"type": "command", "command": command, "timeout": 5})
        added.append(event)

    if not added:
        print("Already installed on SessionEnd and SessionStart.")
        return 0

    f.write_text(json.dumps(cfg, indent=2) + "\n")
    print("Installed capture trigger on " + " and ".join(added) + ".")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
