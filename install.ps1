# One double-click, and everything is ready. The Windows peer of install.sh.
#
# Run it by double-clicking install-cumulate.cmd (in the repo, or made by
# `make-installer.sh ... windows`), or from any PowerShell window:
#
#   irm https://raw.githubusercontent.com/ChazzKemal/cumulate/master/install.ps1 | iex
#
# Neither touches an execution policy. Everything is per-user: no admin rights
# are needed at any point, and nothing needs to be installed beforehand.
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

# The repos are public, so by default this clones them as they are and needs no
# token. `make-installer.sh` can still bake in a token-carrying URL, for a
# private fork; an unbaked placeholder falls back to the public repos.
$CodeRepo    = if ($env:CUMULATE_CODE_REPO)    { $env:CUMULATE_CODE_REPO }    else { "__CODE_REPO__" }
$HarvestRepo = if ($env:CUMULATE_HARVEST_REPO) { $env:CUMULATE_HARVEST_REPO } else { "__HARVEST_REPO__" }
if ($CodeRepo.StartsWith("__"))    { $CodeRepo    = "https://github.com/ChazzKemal/cumulate.git" }
if ($HarvestRepo.StartsWith("__")) { $HarvestRepo = "https://github.com/ChazzKemal/harvest.git" }

# Older Windows 10 builds default to TLS 1.0, which GitHub refuses.
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
$ProgressPreference = "SilentlyContinue"

function Say($m) { Write-Host "  $m" }

# Codex, the assistant everything runs on, is built for 64-bit Windows 10 and 11
# only. Say so up front, rather than failing halfway with something cryptic.
# `return`, not `exit`: run as `irm ... | iex`, exit would close their window.
$os = [Environment]::OSVersion.Version
$is64 = [Environment]::Is64BitOperatingSystem
if ($os.Major -lt 10 -or -not $is64) {
  $name = (Get-CimInstance Win32_OperatingSystem).Caption
  Say "Cumulate needs 64-bit Windows 10 or 11. This computer has $name ($(if ($is64) { '64' } else { '32' })-bit)."
  Say "Nothing has been installed."
  return
}
# Codex supports Windows 10 only when it is fully updated (22H2, build 19045).
if ($os.Build -lt 19045) {
  Say "This Windows 10 is not fully updated. Cumulate will install, but if the"
  Say "assistant misbehaves, run Windows Update and try again."
  Say ""
}

# No Git? Bring a private one: MinGit, unzipped under %LOCALAPPDATA%. No
# installer, no admin, no PATH change that outlives this window -
# bootstrap.bat puts it on PATH for every launch.
$GitDir = Join-Path $env:LOCALAPPDATA "Cumulate\git"
if (Test-Path (Join-Path $GitDir "cmd\git.exe")) { $env:PATH = "$GitDir\cmd;$env:PATH" }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Say "Getting Git (one moment)..."
  $arch = if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") { "arm64" } else { "64-bit" }
  $release = Invoke-RestMethod "https://api.github.com/repos/git-for-windows/git/releases/latest" -UseBasicParsing
  $asset = $release.assets | Where-Object { $_.name -like "MinGit-*-$arch.zip" -and $_.name -notlike "*busybox*" } | Select-Object -First 1
  if (-not $asset) { throw "Couldn't find a Git download. Check your internet connection and try again." }
  $zip = Join-Path $env:TEMP "cumulate-mingit.zip"
  Invoke-WebRequest $asset.browser_download_url -OutFile $zip -UseBasicParsing
  if (Test-Path $GitDir) { Remove-Item -Recurse -Force $GitDir }
  Expand-Archive -Force $zip $GitDir
  Remove-Item $zip -ErrorAction SilentlyContinue
  $env:PATH = "$GitDir\cmd;$env:PATH"
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
