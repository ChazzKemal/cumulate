#!/bin/sh
# One line, and everything is ready.
#
#   curl -fsSL <this file> | bash
#
# Creates ~/Cumulate for the person's own work, puts the shared code somewhere
# separate so updates can never collide with it, and leaves a Start file to
# double-click. Safe to re-run: it updates instead of reinstalling.

set -e

APP_DIR="${CUMULATE_APP:-$HOME/.cumulate/app}"
HARVEST_DIR_="${HARVEST_DIR:-$HOME/.cumulate/Harvest}"
WORKSPACE="${CUMULATE_WORKSPACE:-$HOME/Cumulate}"

# Baked in by `make-installer.sh`. Read-only, scoped to these two repos, and
# revocable on its own — it can clone and nothing else.
CODE_REPO="${CUMULATE_CODE_REPO:-__CODE_REPO__}"
HARVEST_REPO="${CUMULATE_HARVEST_REPO:-__HARVEST_REPO__}"

say() { printf '  %s\n' "$1"; }

command -v git >/dev/null 2>&1 || {
  say "This needs Git. Install Xcode Command Line Tools and run this again:"
  say "  xcode-select --install"
  exit 1
}

get() {  # repo, dir, name
  if [ -d "$2/.git" ]; then
    say "Updating $3…"
    git -C "$2" pull --quiet --ff-only 2>/dev/null || true
  else
    say "Getting $3…"
    mkdir -p "$(dirname "$2")"
    git clone --quiet --depth 1 "$1" "$2"
  fi
}

get "$CODE_REPO" "$APP_DIR" "the tool builder"
get "$HARVEST_REPO" "$HARVEST_DIR_" "the record"

# The workspace: theirs, and never touched by an update.
if [ ! -d "$WORKSPACE" ]; then
  say "Making your Cumulate folder…"
  mkdir -p "$WORKSPACE/inbox" "$WORKSPACE/tools" "$WORKSPACE/projects"
  # Marks the folder as a workspace, so everything can find it from anywhere.
  printf 'This folder is yours. Tools you build and files you drop in live here.\n' \
    > "$WORKSPACE/.cumulate-workspace"
  printf 'inbox/\nprojects/\n.env\n' > "$WORKSPACE/.gitignore"
  cp "$APP_DIR/.env.example" "$WORKSPACE/.env" 2>/dev/null || true
  # Its own history, so the record of what was built is theirs and an update
  # to the shared code can never conflict with it.
  git -C "$WORKSPACE" init --quiet
fi

# One thing to double-click, sitting in their own folder.
cat > "$WORKSPACE/Start.command" <<LAUNCH
#!/bin/sh
export CUMULATE_APP="$APP_DIR"
export HARVEST_DIR="$HARVEST_DIR_"
export CUMULATE_WORKSPACE="$WORKSPACE"
cd "\$(dirname "\$0")" || exit 1
exec "\$CUMULATE_APP/start.command"
LAUNCH
chmod +x "$WORKSPACE/Start.command"

# macOS blocks files it thinks came from the internet. Clear it so the first
# double-click just works instead of showing a scary dialog.
xattr -d com.apple.quarantine "$WORKSPACE/Start.command" 2>/dev/null || true

say ""
say "Done. Open your Cumulate folder and double-click Start."
open "$WORKSPACE" 2>/dev/null || true
