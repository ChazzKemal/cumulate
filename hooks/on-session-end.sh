#!/bin/sh
# Fired by Codex on SessionEnd (arg: end) and SessionStart (arg: start).
# Kicks off knowledge extraction and returns immediately — the hook has a hard
# timeout and must never make anyone wait.
#
# Reinstall with ./install-hooks.sh if `entire enable --force` ever wipes it.

EVENT="${1:-start}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
HARVEST="${HARVEST_DIR:-$(cd "$REPO/../Harvest" 2>/dev/null && pwd)}"
LOG="$REPO/.harvest.log"

[ -n "$HARVEST" ] && [ -x "$HARVEST/.venv/bin/python" ] || exit 0

# On SessionEnd, Codex hands us the session on stdin. Knowing which session just
# finished is the only reliable way to tell "done" from "idle for a moment" —
# Entire reports both as `idle`.
ENDED=""
if [ "$EVENT" = "end" ]; then
  ENDED=$(timeout 2 cat 2>/dev/null | python3 -c 'import json,sys
try:
    d = json.load(sys.stdin)
    print(d.get("session_id") or d.get("sessionId") or "")
except Exception:
    print("")' 2>/dev/null)
fi

printf '\n--- %s (%s%s) ---\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$EVENT" \
  "${ENDED:+ $(echo "$ENDED" | cut -c1-8)}" >>"$LOG"

# Detach completely: no stdin, output to the log, survives the session closing.
# `-m harvest` resolves from Harvest's own directory, so run from there.
( cd "$HARVEST" && nohup "$HARVEST/.venv/bin/python" -u -m harvest run \
    --repo "$REPO" ${ENDED:+--ended "$ENDED"} >>"$LOG" 2>&1 </dev/null & )

exit 0
