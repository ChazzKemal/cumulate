#!/bin/sh
# Gets a machine ready. Idempotent — runs on every launch, does nothing when
# everything is already in place.
#
# Everything it says out loud is written for someone who has never opened a
# terminal. No package names, no versions, no paths. If a step fails, it says
# what to do next in one sentence.

set -e
# The venv and dependencies belong to the code, not to the person's folder.
ROOT="${CUMULATE_APP:-$(cd "$(dirname "$0")/.." && pwd)}"
WORKSPACE="${CUMULATE_WORKSPACE:-$ROOT}"
cd "$ROOT"

# Take any update to the shared code before starting. Nothing here is edited by
# anyone, so a pull cannot conflict — their own work lives elsewhere.
if [ -d "$ROOT/.git" ] && [ "$ROOT" != "$WORKSPACE" ]; then
  git -C "$ROOT" pull --quiet --ff-only 2>/dev/null || true
  [ -d "${HARVEST_DIR:-}" ] && git -C "$HARVEST_DIR" pull --quiet --ff-only 2>/dev/null || true
fi

say() { printf '  %s\n' "$1"; }

# --- the runner --------------------------------------------------------------
if ! command -v uv >/dev/null 2>&1; then
  say "Setting up (one moment)…"
  curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1 || {
    say "Couldn't finish setup. Check your internet connection and try again."
    exit 1
  }
fi
# The installer drops it here but the current shell may not know that yet.
[ -x "$HOME/.local/bin/uv" ] && PATH="$HOME/.local/bin:$PATH"
export PATH

# --- the workspace's own tools ----------------------------------------------
if [ ! -x ".venv/bin/python" ]; then
  say "Getting things ready. This takes a minute the first time…"
  uv venv --python 3.12 >/dev/null 2>&1
  uv pip install -q -r requirements.txt >/dev/null 2>&1
  say "…ready."
fi

# Dependencies change as tools grow; keep them current without a visible step.
uv pip install -q -r requirements.txt >/dev/null 2>&1 || true

# --- the assistant -----------------------------------------------------------
CODEX_WAS_MISSING=0
if ! command -v codex >/dev/null 2>&1; then
  CODEX_WAS_MISSING=1
  say "Installing the assistant. This can take a few minutes on a first"
  say "run — the window is not frozen, it is downloading…"
  if command -v npm >/dev/null 2>&1; then
    npm install -g @openai/codex >/dev/null 2>&1 || true
  elif command -v brew >/dev/null 2>&1; then
    brew install codex >/dev/null 2>&1 || true
  fi
fi
if command -v codex >/dev/null 2>&1; then
  [ "$CODEX_WAS_MISSING" = 1 ] && say "…assistant installed." || true
else
  say "The assistant could not be installed automatically."
  say "Ask whoever set this up for you to finish it — they'll know what to do."
  exit 1
fi

# --- session recording -------------------------------------------------------
# Without this nothing is captured, so the knowledge record stays empty and
# "My sessions" has nothing to show. Not optional, but never worth explaining.
if ! command -v entire >/dev/null 2>&1; then
  say "Setting up session recording (another short download)…"
  # Homebrew is the documented route on macOS; the script is documented for
  # Linux and is what put it on this machine. Try the right one first, fall
  # back to the other, and carry on either way — a missing recorder should
  # never stop someone getting their work done.
  if [ "$(uname -s)" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
    brew tap entireio/tap >/dev/null 2>&1 && brew trust entireio/tap >/dev/null 2>&1
    brew install --cask entire >/dev/null 2>&1 || true
  fi
  command -v entire >/dev/null 2>&1 || \
    curl -fsSL https://entire.io/install.sh 2>/dev/null | bash >/dev/null 2>&1 || true
  [ -x "$HOME/.local/bin/entire" ] && PATH="$HOME/.local/bin:$PATH"
  export PATH
fi

if command -v entire >/dev/null 2>&1; then
  [ -f "$WORKSPACE/.entire/settings.json" ] || (cd "$WORKSPACE" && entire enable --agent codex) >/dev/null 2>&1 || true
fi
say "Setup complete. Opening your workspace…"
# The capture hook is plain Python — install it whether or not entire made it.
[ -f "$WORKSPACE/.codex/hooks.json" ] && (cd "$WORKSPACE" && "$ROOT/.venv/bin/python" "$ROOT/scaffold/install_hooks.py") >/dev/null 2>&1 || true
