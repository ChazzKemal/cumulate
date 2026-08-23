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

clear
exec codex "Check the inbox folder for spreadsheets. Greet me in one line and ask what I need built."
