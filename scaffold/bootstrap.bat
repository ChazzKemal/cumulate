@echo off
rem Gets a machine ready. Idempotent - runs on every launch, does nothing when
rem everything is already in place. Mirrors scaffold/bootstrap.sh.
rem
rem Everything here is per-user: nothing needs admin rights, because the person
rem running it will not have them. No setlocal, deliberately - the PATH entries
rem added here must still be there when start.bat looks for codex and entire.
rem
rem The venv and dependencies belong to the code, not to the person's folder.
if not defined CUMULATE_APP set "CUMULATE_APP=%~dp0.."
cd /d "%CUMULATE_APP%"
if not defined CUMULATE_WORKSPACE set "CUMULATE_WORKSPACE=%CD%"

rem Take any update to the shared code before starting. Nothing here is edited
rem by anyone, so a pull cannot conflict - their own work lives elsewhere.
if not exist ".git" goto pulled
if /i "%CD%"=="%CUMULATE_WORKSPACE%" goto pulled
git pull --quiet --ff-only >nul 2>&1
if defined HARVEST_DIR git -C "%HARVEST_DIR%" pull --quiet --ff-only >nul 2>&1
:pulled

rem --- the runner ---------------------------------------------------------
where uv >nul 2>&1
if errorlevel 1 (
  echo   Setting up ^(one moment^)...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex" >nul 2>&1
)
rem The installer drops it here but the current session may not know that yet.
set "PATH=%USERPROFILE%\.local\bin;%PATH%"

where uv >nul 2>&1
if errorlevel 1 (
  echo   Couldn't finish setup. Check your internet connection and try again.
  pause
  exit /b 1
)

rem --- the workspace's own tools --------------------------------------------
if not exist ".venv\Scripts\python.exe" (
  echo   Getting things ready. This takes a minute the first time...
  uv venv --python 3.12 >nul 2>&1
  echo   ...ready.
)
rem Dependencies change as tools grow; keep them current without a visible step.
uv pip install -q -r requirements.txt >nul 2>&1

rem Harvest keeps its own venv - the viewer and capture both need it.
if not defined HARVEST_DIR goto harvestdone
if not exist "%HARVEST_DIR%\requirements.txt" goto harvestdone
if exist "%HARVEST_DIR%\.venv\Scripts\python.exe" goto harvestdone
echo   Preparing the session recorder...
pushd "%HARVEST_DIR%"
uv venv --python 3.12 >nul 2>&1
uv pip install -q -r requirements.txt >nul 2>&1
popd
:harvestdone

rem --- the assistant ---------------------------------------------------------
rem npm when the machine has it; otherwise the release binary, which needs no
rem package manager, no PATH changes that outlive this window, and no admin.
set "CUMULATE_BIN=%LOCALAPPDATA%\Cumulate\bin"
if exist "%CUMULATE_BIN%\codex.exe" set "PATH=%CUMULATE_BIN%;%PATH%"
where codex >nul 2>&1
if not errorlevel 1 goto codexok

echo   Installing the assistant. This can take a few minutes on a first
echo   run - the window is not frozen, it is downloading...
where npm >nul 2>&1
if errorlevel 1 goto codexbinary
call npm install -g @openai/codex
where codex >nul 2>&1
if not errorlevel 1 goto codexinstalled
echo   That route didn't work - trying a direct download instead...

:codexbinary
if not exist "%CUMULATE_BIN%" mkdir "%CUMULATE_BIN%" >nul 2>&1
set "CODEX_ARCH=x86_64"
if /i "%PROCESSOR_ARCHITECTURE%"=="ARM64" set "CODEX_ARCH=aarch64"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://github.com/openai/codex/releases/latest/download/codex-%CODEX_ARCH%-pc-windows-msvc.exe' -OutFile '%CUMULATE_BIN%\codex.exe'" >nul 2>&1
set "PATH=%CUMULATE_BIN%;%PATH%"

where codex >nul 2>&1
if not errorlevel 1 goto codexinstalled
echo   The assistant could not be installed automatically.
echo   Check your internet connection and try again.
pause
exit /b 1
:codexinstalled
echo   ...assistant installed.
:codexok

rem --- session recording ------------------------------------------------------
rem Without this nothing is captured, so "My sessions" stays empty. Scoop is the
rem documented route on Windows, but it refuses some accounts (administrators),
rem so fall back to the release zip - per-user, no package manager, like codex.
rem If any of this fails, carry on - a missing recorder must never stop someone
rem getting their work done.
set "PATH=%USERPROFILE%\scoop\shims;%PATH%"
where entire >nul 2>&1
if not errorlevel 1 goto entiredone

echo   Setting up session recording ^(another short download^)...
where scoop >nul 2>&1
if not errorlevel 1 goto haveScoop
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm get.scoop.sh | iex" >nul 2>&1
where scoop >nul 2>&1
if errorlevel 1 goto entirebinary

:haveScoop
call scoop bucket add entire https://github.com/entireio/scoop-bucket.git >nul 2>&1
call scoop install entire/entire >nul 2>&1
where entire >nul 2>&1
if not errorlevel 1 goto entiredone

:entirebinary
if not exist "%CUMULATE_BIN%" mkdir "%CUMULATE_BIN%" >nul 2>&1
set "ENTIRE_ARCH=amd64"
if /i "%PROCESSOR_ARCHITECTURE%"=="ARM64" set "ENTIRE_ARCH=arm64"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://github.com/entireio/cli/releases/latest/download/entire_windows_%ENTIRE_ARCH%.zip' -OutFile \"$env:TEMP\entire.zip\"; Expand-Archive -Force \"$env:TEMP\entire.zip\" \"$env:TEMP\entire_unzip\"; Copy-Item \"$env:TEMP\entire_unzip\entire.exe\",\"$env:TEMP\entire_unzip\git-remote-entire.exe\" '%CUMULATE_BIN%' -Force" >nul 2>&1
set "PATH=%CUMULATE_BIN%;%PATH%"
:entiredone

cd /d "%CUMULATE_WORKSPACE%"
where entire >nul 2>&1
if errorlevel 1 (
  echo   Session recording is not available on this machine. Carrying on.
) else (
  if not exist ".entire\settings.json" entire enable --agent codex >nul 2>&1
)
echo   Setup complete. Opening your workspace...
rem The capture hook is plain Python - install it whether or not entire made it.
if exist ".codex\hooks.json" "%CUMULATE_APP%\.venv\Scripts\python.exe" "%CUMULATE_APP%\scaffold\install_hooks.py" >nul 2>&1
exit /b 0
