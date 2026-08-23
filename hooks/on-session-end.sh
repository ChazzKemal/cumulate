#!/bin/sh
# Fired when a Codex session ends. Kicks off knowledge extraction and returns
# immediately — the hook has a hard timeout and must never make anyone wait.
#
# Reinstall with ./install-hooks.sh if `entire enable --force` ever wipes it.

REPO="$(cd "$(dirname "$0")/.." && pwd)"
HARVEST="${HARVEST_DIR:-$(cd "$REPO/../Harvest" 2>/dev/null && pwd)}"
LOG="$REPO/.harvest.log"

[ -n "$HARVEST" ] && [ -x "$HARVEST/.venv/bin/python" ] || exit 0

# Detach completely: no stdin, output to the log, survives the session closing.
# `-m harvest` resolves from Harvest's own directory, so run from there.
printf '\n--- %s ---\n' "$(date '+%Y-%m-%d %H:%M:%S')" >>"$LOG"
( cd "$HARVEST" && nohup "$HARVEST/.venv/bin/python" -m harvest run --repo "$REPO" \
    >>"$LOG" 2>&1 </dev/null & )

exit 0
