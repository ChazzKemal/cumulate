#!/bin/sh
# Produces the installer you send someone, with a read-only token baked in.
#
#   ./make-installer.sh <token> you/cumulate you/harvest \
#       > ~/Desktop/install-cumulate.command && chmod +x ~/Desktop/install-cumulate.command
#
#   ./make-installer.sh <token> you/cumulate you/harvest windows \
#       > ~/Desktop/install-cumulate.cmd
#
# Name the macOS one .command, not .sh — double-clicking a .sh on macOS opens
# it in a text editor. A .command runs in Terminal, which is what someone
# expects.
#
# The Windows one is a .cmd for the same reason: a .ps1 will not run on
# double-click, and Set-ExecutionPolicy may be locked by the person's IT.
# The .cmd re-runs itself through PowerShell with a process-scoped bypass,
# which needs no admin rights and changes no policy.
#
# The repos stay private. The token is a fine-grained GitHub token with
# Contents: read-only on those two repos and nothing else — it can clone them
# and do nothing more, and you can revoke it on its own without touching
# anyone else's.
#
# Be clear-eyed: the token sits in a file on their machine and they can read it.
# That is unavoidable for a private repo with no account on their side. Scope it
# to read-only, give one per person if you want individual revoking, and rotate
# it if someone leaves.

set -e
TOKEN="$1"; CODE="$2"; HARVEST="$3"; PLATFORM="$4"

if [ -z "$TOKEN" ] || [ -z "$CODE" ] || [ -z "$HARVEST" ]; then
  echo "usage: ./make-installer.sh <github-token> <owner/code-repo> <owner/harvest-repo> [windows]" >&2
  exit 1
fi

bake() {
  sed \
    -e "s|__CODE_REPO__|https://x-access-token:${TOKEN}@github.com/${CODE}.git|" \
    -e "s|__HARVEST_REPO__|https://x-access-token:${TOKEN}@github.com/${HARVEST}.git|" \
    "$(dirname "$0")/$1"
}

if [ "$PLATFORM" != "windows" ]; then
  bake install.sh
  exit 0
fi

# A cmd/PowerShell polyglot: to cmd, the first line is a label and the block
# below runs; to PowerShell, everything up to #> is a comment and the baked
# install.ps1 is the script. One file, double-clickable, no policy changes.
printf '%s\r\n' \
  '<# : batch portion' \
  '@echo off' \
  'powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-Expression ([System.IO.File]::ReadAllText('"'"'%~f0'"'"'))"' \
  'pause' \
  'exit /b' \
  '#>'
bake install.ps1 | sed 's/$/\r/'
