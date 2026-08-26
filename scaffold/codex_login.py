"""Hand the key to the assistant. Idempotent.

The key alone is not enough: it is ignored unless it has been handed over
explicitly, and without that a fresh machine drops someone into a sign-in
screen seconds after the welcome page told them they were finished.

Python rather than shell for the same reason as install_hooks.py — one copy
that behaves the same everywhere, and no piping a secret through a shell that
would append a stray newline to it.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path(os.environ.get("CUMULATE_WORKSPACE") or Path.cwd())
APP = Path(os.environ.get("CUMULATE_APP") or Path(__file__).resolve().parent.parent)


def _key() -> str:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if key:
        return key
    for env in (WORKSPACE / ".env", APP / ".env"):
        if not env.exists():
            continue
        for line in env.read_text().splitlines():
            if line.startswith("OPENAI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _codex() -> str | None:
    # On Windows the assistant is a .cmd shim, which is not found unless the
    # full name is resolved first.
    return shutil.which("codex")


def _logged_in(codex: str) -> bool:
    try:
        out = subprocess.run([codex, "login", "status"], capture_output=True,
                             text=True, timeout=20)
    except Exception:
        return False
    return "not logged in" not in (out.stdout + out.stderr).lower()


def main() -> int:
    codex = _codex()
    if codex is None or _logged_in(codex):
        return 0
    key = _key()
    if not key:
        return 0
    try:
        subprocess.run([codex, "login", "--with-api-key"], input=key,
                       text=True, capture_output=True, timeout=60)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
