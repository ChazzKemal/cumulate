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

# Also surface anything they saved recently — most people never move files.
RECENT=$(find "$HOME/Desktop" "$HOME/Downloads" -maxdepth 1 -type f -mtime -7 \
         \( -iname '*.xlsx' -o -iname '*.xls' -o -iname '*.xlsm' -o -iname '*.csv' \
            -o -iname '*.tsv' -o -iname '*.json' -o -iname '*.jsonl' -o -iname '*.log' \) \
         2>/dev/null | head -6 | paste -sd', ' -)

PROMPT="You are in the Tool Builder project. Follow AGENTS.md."
[ -n "$FILES" ]  && PROMPT="$PROMPT Files in the inbox: ${FILES}."
[ -n "$RECENT" ] && PROMPT="$PROMPT Recently saved elsewhere: ${RECENT}."
if [ -n "$FILES$RECENT" ]; then
  PROMPT="$PROMPT These are gitignored or outside the repo, so file search will not
find them — read them directly by path. Profile the most likely one with
scaffold/ingest.py, say in plain language what you found, and ask what I need built."
else
  PROMPT="$PROMPT Greet me in one line and ask what I need built. Mention I can drag a
file straight onto this window or drop it in the inbox folder."
fi

echo
echo "  Tip: you can drag a file onto this window instead of moving it."
echo

clear
exec codex "$PROMPT"
