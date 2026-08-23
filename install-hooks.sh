#!/bin/sh
# Adds the harvest trigger to Codex's SessionEnd, next to Entire's own hook.
# Idempotent. Re-run after `entire enable --force`.
cd "$(dirname "$0")" || exit 1
python3 - "$@" <<'PY'
import json, pathlib, sys

f = pathlib.Path(".codex/hooks.json")
if not f.exists():
    sys.exit("No .codex/hooks.json — run `entire enable --agent codex` first.")

cfg = json.loads(f.read_text())
def cmd_for(event):
    arg = "end" if event == "SessionEnd" else "start"
    return ("sh -c '\"$(git rev-parse --show-toplevel)/hooks/on-session-end.sh\" "
            + arg + "'")
events = cfg.setdefault("hooks", {})

# SessionEnd is the normal trigger. SessionStart is the safety net: if a session
# was killed hard and SessionEnd never fired, the next one sweeps it up.
added = []
for event in ("SessionEnd", "SessionStart"):
    group = events.setdefault(event, [{"matcher": None, "hooks": []}])
    if any("on-session-end.sh" in h.get("command", "") for g in group for h in g.get("hooks", [])):
        continue
    group[0].setdefault("hooks", []).append(
        {"type": "command", "command": cmd_for(event), "timeout": 5})
    added.append(event)

if not added:
    print("Already installed on SessionEnd and SessionStart.")
    sys.exit(0)

f.write_text(json.dumps(cfg, indent=2) + "\n")
print("Installed harvest trigger on " + " and ".join(added) + ".")
PY
