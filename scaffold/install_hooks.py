"""Install the capture trigger into Codex's hooks. Idempotent.

Python rather than shell so it runs on Windows too, and so the hook it installs
needs no shell either — the old version wired in `sh -c ...`, which simply never
fired on a Windows machine.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

import os

# The hook lives with the code; it is installed into the person's workspace.
APP = Path(os.environ.get("CUMULATE_APP") or Path(__file__).resolve().parent.parent)
ROOT = Path(os.environ.get("CUMULATE_WORKSPACE") or APP)


def _cmd_path(p: Path) -> str:
    """A path usable inside a Codex hook command on this OS.

    Codex's Windows hook runner passes commands through `cmd.exe /C "..."`,
    whose quote stripping mangles any command that quotes its executable —
    the hook then fails before running anything. Paths must therefore go in
    unquoted; when one contains a space, its 8.3 short form is used instead.
    """
    if os.name != "nt":
        return f'"{p}"'
    s = str(p)
    if " " not in s:
        return s
    import ctypes

    buf = ctypes.create_unicode_buffer(260)
    if ctypes.windll.kernel32.GetShortPathNameW(s, buf, 260):
        return buf.value
    return s


def _fix_entire_hooks(events: dict) -> bool:
    """Rewrite entire's `sh -c ...` hooks into a form Windows can run.

    `entire enable` emits POSIX shell wrappers; cmd.exe has no `sh`, so on
    Windows every one of them fails. The wrapper only guards against a
    missing binary, so replace it with a direct call to the entire that is
    installed right now.
    """
    if os.name != "nt":
        return False
    entire = shutil.which("entire")
    if not entire:
        return False
    exe = _cmd_path(Path(entire))
    changed = False
    for group in events.values():
        for g in group:
            for h in g.get("hooks", []):
                cmd = h.get("command", "")
                m = re.search(r"entire hooks ([\w-]+(?: [\w-]+)*)", cmd)
                if cmd.startswith("sh -c") and "entire hooks" in cmd and m:
                    h["command"] = f"{exe} hooks {m.group(1)}"
                    changed = True
    return changed


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
        command = f"{_cmd_path(Path(sys.executable))} {_cmd_path(hook)} {arg}"
        group = events.setdefault(event, [{"matcher": None, "hooks": []}])
        if any(h.get("command") == command
               for g in group for h in g.get("hooks", [])):
            continue
        # A capture entry pointing anywhere else is from another machine or an
        # old install — its interpreter does not exist here, so it never fires.
        # Replace it rather than treating it as already installed.
        for g in group:
            g["hooks"] = [h for h in g.get("hooks", [])
                          if "on_session_end" not in h.get("command", "")
                          and "on-session-end" not in h.get("command", "")]
        group[0].setdefault("hooks", []).append(
            {"type": "command", "command": command, "timeout": 5})
        added.append(event)

    fixed_entire = _fix_entire_hooks(events)

    if not added and not fixed_entire:
        print("Already installed on SessionEnd and SessionStart.")
        return 0

    f.write_text(json.dumps(cfg, indent=2) + "\n")
    if added:
        print("Installed capture trigger on " + " and ".join(added) + ".")
    if fixed_entire:
        print("Adapted entire's hooks for Windows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
