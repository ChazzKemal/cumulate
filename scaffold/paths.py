"""Where things are. One answer, so the layout is not re-guessed in every file.

Two directories, deliberately separate:

  the app        — scaffold, hooks, launcher, the code everyone shares. Updated
                   by pulling; nobody edits it, so a pull can never conflict.
  the workspace  — inbox/, tools/, projects/, ASSUMPTIONS.md, .env. One person's
                   own work, with its own git history for Entire to track.

Keeping tools in the same repo as the code was what made updates impossible:
shipping a fix would collide with whatever the person had built that week.
"""
from __future__ import annotations

import os
from pathlib import Path

APP = Path(os.environ.get("CUMULATE_APP") or Path(__file__).resolve().parent.parent)


def workspace() -> Path:
    """Where this person's own work lives."""
    if w := os.environ.get("CUMULATE_WORKSPACE"):
        return Path(w).expanduser()
    # A workspace marks itself, so running from inside one just works.
    here = Path.cwd()
    for d in (here, *here.parents):
        if (d / ".cumulate-workspace").exists():
            return d
    # Older single-folder setups, where the app and the workspace are the same
    # directory. Keeps existing installs working.
    return APP


# Kept as a name because modules already import it; it now means the workspace.
WORKSPACE = workspace()


def harvest_dir() -> Path:
    return Path(os.environ.get("HARVEST_DIR") or APP.parent / "Harvest")


def harvest_out() -> Path:
    return harvest_dir() / "out"


def tools_dir() -> Path:
    return workspace() / "tools"


def inbox_dir() -> Path:
    return workspace() / "inbox"
