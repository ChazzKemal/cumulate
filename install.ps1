# One double-click, and everything is ready. The Windows peer of install.sh.
#
# Sent to someone as install-cumulate.cmd (made by `make-installer.sh ... windows`),
# which runs this without anyone touching an execution policy. Everything is
# per-user: no admin rights are needed at any point.
#
# The app and the record live under %LOCALAPPDATA% — a local disk, short paths,
# never synced — because a venv inside OneDrive gets corrupted by sync and a
# profile on a network share breaks it outright. Only the person's own work
# goes in their profile, where they can see it.
#
# Safe to re-run: it updates instead of reinstalling.

$ErrorActionPreference = "Stop"

$AppDir     = if ($env:CUMULATE_APP)       { $env:CUMULATE_APP }       else { Join-Path $env:LOCALAPPDATA "Cumulate\app" }
$HarvestDir = if ($env:HARVEST_DIR)        { $env:HARVEST_DIR }        else { Join-Path $env:LOCALAPPDATA "Cumulate\Harvest" }
$Workspace  = if ($env:CUMULATE_WORKSPACE) { $env:CUMULATE_WORKSPACE } else { Join-Path $env:USERPROFILE "Cumulate" }

# Baked in by `make-installer.sh`. Read-only, scoped to these two repos, and
# revocable on its own — it can clone and nothing else.
$CodeRepo    = if ($env:CUMULATE_CODE_REPO)    { $env:CUMULATE_CODE_REPO }    else { "__CODE_REPO__" }
$HarvestRepo = if ($env:CUMULATE_HARVEST_REPO) { $env:CUMULATE_HARVEST_REPO } else { "__HARVEST_REPO__" }

function Say($m) { Write-Host "  $m" }

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Say "This needs Git. Install it for just your account (no admin password needed):"
  Say ""
  Say "    winget install --scope user Git.Git"
  Say ""
  Say "then close this window and run the installer again."
  exit 1
}

function Get-Repo($repo, $dir, $name) {
  if (Test-Path (Join-Path $dir ".git")) {
    Say "Updating $name..."
    git -C $dir pull --quiet --ff-only 2>$null | Out-Null
  } else {
    Say "Getting $name..."
    New-Item -ItemType Directory -Force -Path (Split-Path $dir) | Out-Null
    git clone --quiet --depth 1 $repo $dir
  }
}

Get-Repo $CodeRepo $AppDir "the tool builder"
Get-Repo $HarvestRepo $HarvestDir "the record"

# The workspace: theirs, and never touched by an update.
if (-not (Test-Path $Workspace)) {
  Say "Making your Cumulate folder..."
  foreach ($d in "inbox", "tools", "projects") {
    New-Item -ItemType Directory -Force -Path (Join-Path $Workspace $d) | Out-Null
  }
  # Marks the folder as a workspace, so everything can find it from anywhere.
  Set-Content -Path (Join-Path $Workspace ".cumulate-workspace") `
    -Value "This folder is yours. Tools you build and files you drop in live here."
  Set-Content -Path (Join-Path $Workspace ".gitignore") -Value "inbox/`nprojects/`n.env"
  if (Test-Path (Join-Path $AppDir ".env.example")) {
    Copy-Item (Join-Path $AppDir ".env.example") (Join-Path $Workspace ".env")
  }
  # Its own history, so the record of what was built is theirs and an update
  # to the shared code can never conflict with it.
  git -C $Workspace init --quiet
}

# One thing to double-click, sitting in their own folder.
$startCmd = @"
@echo off
set "CUMULATE_APP=$AppDir"
set "HARVEST_DIR=$HarvestDir"
set "CUMULATE_WORKSPACE=$Workspace"
call "%CUMULATE_APP%\start.bat"
"@
Set-Content -Path (Join-Path $Workspace "Start.cmd") -Value $startCmd -Encoding ASCII

# Windows blocks files it thinks came from the internet. Clear the mark so the
# first double-click just works instead of showing a warning.
Unblock-File -Path (Join-Path $Workspace "Start.cmd") -ErrorAction SilentlyContinue

Say ""
Say "Done. Open your Cumulate folder and double-click Start."
Start-Process explorer.exe $Workspace
