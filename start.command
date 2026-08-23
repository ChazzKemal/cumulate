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

if [ -n "$FILES" ]; then
  PROMPT="Files waiting in the inbox: ${FILES}. These are gitignored so file search
will not find them — read them directly by path. Profile the first one with
scaffold/ingest.py, tell me in plain language what you found, and ask what I need built."
else
  PROMPT="The inbox is empty. Greet me in one line and ask what I need built,
and mention they can drop a spreadsheet into the inbox folder."
fi

clear
exec codex "$PROMPT"
