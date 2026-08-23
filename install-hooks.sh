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
cmd = "sh -c '\"$(git rev-parse --show-toplevel)/hooks/on-session-end.sh\"'"
events = cfg.setdefault("hooks", {})
group = events.setdefault("SessionEnd", [{"matcher": None, "hooks": []}])

existing = [h for g in group for h in g.get("hooks", []) if "on-session-end.sh" in h.get("command", "")]
if existing:
    print("Already installed.")
    sys.exit(0)

group[0].setdefault("hooks", []).append({"type": "command", "command": cmd, "timeout": 5})
f.write_text(json.dumps(cfg, indent=2) + "\n")
print("Installed harvest trigger on SessionEnd.")
PY
