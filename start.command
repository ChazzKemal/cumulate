#!/bin/bash
# Double-click this to start. Nothing to install, nothing to type.
cd "$(dirname "$0")" || exit 1

if [ -f .env ]; then
  set -a; . ./.env; set +a
fi

if [ -z "$OPENAI_API_KEY" ]; then
  clear
  echo
  echo "  One-time setup needed."
  echo
  echo "  Open the file called  .env.example  in this folder,"
  echo "  paste your OpenAI key in, and save it as  .env"
  echo
  echo "  Then double-click this again."
  echo
  read -r -p "  Press return to close."
  exit 1
fi

# inbox/ is gitignored, so file search can't see it. List it explicitly
# and hand the names to the agent so it can never miss them.
FILES=$(find inbox -maxdepth 1 -type f ! -name '.*' -exec basename {} \; 2>/dev/null \
        | sort | sed 's|^|inbox/|' | paste -sd', ' -)

PY="${PWD}/.venv/bin/python"
[ -x "$PY" ] || PY=python3
TOOLS_HUMAN=$("$PY" scaffold/tools_index.py 2>/dev/null)
TOOLS_PROMPT=$("$PY" scaffold/tools_index.py --prompt 2>/dev/null)

PROMPT="You are in the Tool Builder project. Follow AGENTS.md."
[ -n "$FILES" ] && PROMPT="$PROMPT Files sitting in the inbox: ${FILES} (gitignored, so
file search will not find them — read them by path when the time comes)."
[ -n "$TOOLS_PROMPT" ] && PROMPT="$PROMPT ${TOOLS_PROMPT}"
PROMPT="$PROMPT Greet me in one line, say what is in the inbox if anything, and ask what
I need. Do not open, read or profile any file yet — wait until I have told you what I
want."

clear
echo
echo "  Tools you already have:"
echo
echo "${TOOLS_HUMAN:-  none yet}"
echo
echo "  Drag a file onto this window, or drop it in the inbox folder."
echo

clear
exec codex "$PROMPT"
