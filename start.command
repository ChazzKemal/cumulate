#!/bin/bash
# Double-click this to start. Nothing to install, nothing to type.
# The code and the person's own work live in different places, so that updating
# one can never disturb the other. APP is the code; WORKSPACE is theirs.
APP="${CUMULATE_APP:-$(cd "$(dirname "$0")" && pwd)}"
WORKSPACE="${CUMULATE_WORKSPACE:-$APP}"
export CUMULATE_APP CUMULATE_WORKSPACE
CUMULATE_APP="$APP"; CUMULATE_WORKSPACE="$WORKSPACE"
cd "$WORKSPACE" || exit 1

# Fresh machine? Get everything in place first. Does nothing when it already is.
sh "$APP/scaffold/bootstrap.sh" || exit 1

# Shared connection settings ship with the code; personal ones live with the
# person and override them.
[ -f "$APP/config.env" ] && { set -a; . "$APP/config.env"; set +a; }
if [ -f "$WORKSPACE/.env" ]; then
  set -a; . "$WORKSPACE/.env"; set +a
elif [ -f "$APP/.env" ]; then
  set -a; . "$APP/.env"; set +a
fi

# Someone needs setting up only if they have no key. Signing in is how a key
# is issued, so a key already in .env means they are ready — never send them
# back through the browser for it.
NEEDS_SETUP=""
[ -z "$OPENAI_API_KEY" ] && NEEDS_SETUP=1

if [ -n "$NEEDS_SETUP" ]; then
  # No key yet: open the welcome page and wait. Signing in there writes the key
  # and this picks it up — nobody edits a file, nobody pastes anything.
  clear
  echo
  echo "  Opening your browser to get you set up…"
  echo
  ("$APP/.venv/bin/streamlit" run "$APP/scaffold/welcome.py" --server.headless false \
     --server.port 8501 >/dev/null 2>&1 &)
  # Give up after ten minutes rather than hanging forever on a window someone
  # closed, or a sign-in they walked away from.
  WAITED=0
  while [ -n "$NEEDS_SETUP" ] && [ "$WAITED" -lt 600 ]; do
    sleep 2
    WAITED=$((WAITED + 2))
    [ -f .env ] && { set -a; . ./.env; set +a; }
    NEEDS_SETUP=""
    [ -z "$OPENAI_API_KEY" ] && NEEDS_SETUP=1
  done
  pkill -f "scaffold/welcome.py" >/dev/null 2>&1
  if [ -n "$NEEDS_SETUP" ]; then
    clear
    echo
    echo "  Setup didn't finish. Double-click this again when you're ready."
    echo
    read -r -p "  Press return to close."
    exit 1
  fi
  clear
fi

# inbox/ is gitignored, so file search can't see it. List it explicitly
# and hand the names to the agent so it can never miss them.
FILES=$(find inbox -maxdepth 1 -type f ! -name '.*' -exec basename {} \; 2>/dev/null \
        | sort | sed 's|^|inbox/|' | paste -sd', ' -)

PY="$APP/.venv/bin/python"
[ -x "$PY" ] || PY=python3
TOOLS_HUMAN=$("$PY" "$APP/scaffold/tools_index.py" 2>/dev/null)
TOOLS_PROMPT=$("$PY" "$APP/scaffold/tools_index.py" --prompt 2>/dev/null)
# projects/ is gitignored too, for the same reason inbox/ is. Same fix.
PROJECTS_HUMAN=$("$PY" "$APP/scaffold/projects_index.py" 2>/dev/null)
PROJECTS_PROMPT=$("$PY" "$APP/scaffold/projects_index.py" --prompt 2>/dev/null)

PROMPT="You are in the Tool Builder project. Follow AGENTS.md."
[ -n "$FILES" ] && PROMPT="$PROMPT Files sitting in the inbox: ${FILES} (gitignored, so
file search will not find them — read them by path when the time comes)."
[ -n "$TOOLS_PROMPT" ] && PROMPT="$PROMPT ${TOOLS_PROMPT}"
[ -n "$PROJECTS_PROMPT" ] && PROMPT="$PROMPT ${PROJECTS_PROMPT}"
PROMPT="$PROMPT Greet me in one line, say what is in the inbox if anything, and ask what
I need. Do not open, read or profile any file yet — wait until I have told you what I
want."

clear
echo
echo "  Tools you already have:"
echo
echo "${TOOLS_HUMAN:-  none yet}"
echo
echo "  Work you did before this existed:"
echo
echo "${PROJECTS_HUMAN}"
echo
echo "  Drag a file onto this window, or drop it in the inbox folder."
echo
read -r -p "  Press return to begin."

exec codex "$PROMPT"
