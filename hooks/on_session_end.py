"""Fired by Codex on SessionStart and SessionEnd.

Replaces the shell version so it works the same on Windows, where there is no
`sh` and the hook would otherwise never run — meaning nothing captured, and an
empty "My sessions".

Only KEEPS the conversation: free, no model call. Summarising stays deliberate.
Returns immediately — the hook has a hard timeout and must never make anyone
wait — by spawning the real work fully detached.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HARVEST = Path(os.environ.get("HARVEST_DIR") or REPO.parent / "Harvest")
LOG = REPO / ".harvest.log"


def _python() -> Path | None:
    for rel in ("bin/python", "Scripts/python.exe"):
        p = HARVEST / ".venv" / rel
        if p.exists():
            return p
    return None


def main() -> int:
    event = sys.argv[1] if len(sys.argv) > 1 else "start"
    python = _python()
    if python is None:
        return 0

    # On SessionEnd, Codex hands us the session on stdin. Knowing which session
    # just finished is the only reliable way to tell "done" from "idle for a
    # moment" — Entire reports both as idle.
    ended = ""
    if event == "end" and not sys.stdin.isatty():
        try:
            ended = (json.load(sys.stdin) or {}).get("session_id") or ""
        except Exception:
            ended = ""

    cmd = [str(python), "-u", "-m", "harvest", "capture", "--repo", str(REPO)]
    if ended:
        cmd += ["--ended", ended]

    with LOG.open("a") as log:
        log.write(f"\n--- {datetime.now():%Y-%m-%d %H:%M:%S} ({event}"
                  f"{' ' + ended[:8] if ended else ''}) ---\n")
        log.flush()
        # Detach completely, so closing the session cannot kill the capture.
        kwargs = {"stdout": log, "stderr": log, "stdin": subprocess.DEVNULL,
                  "cwd": str(HARVEST)}
        if os.name == "nt":
            kwargs["creationflags"] = (subprocess.CREATE_NEW_PROCESS_GROUP
                                       | getattr(subprocess, "DETACHED_PROCESS", 0))
        else:
            kwargs["start_new_session"] = True
        try:
            subprocess.Popen(cmd, **kwargs)
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
