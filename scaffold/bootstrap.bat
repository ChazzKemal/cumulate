@echo off
rem Gets a machine ready. Idempotent - runs on every launch, does nothing when
rem everything is already in place. Mirrors scaffold/bootstrap.sh.
cd /d "%~dp0.."

where uv >nul 2>&1
if errorlevel 1 (
  echo   Setting up ^(one moment^)...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex" >nul 2>&1
  set "PATH=%USERPROFILE%\.local\bin;%PATH%"
)

where uv >nul 2>&1
if errorlevel 1 (
  echo   Couldn't finish setup. Check your internet connection and try again.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo   Getting things ready. This takes a minute the first time...
  uv venv --python 3.12 >nul 2>&1
)
uv pip install -q -r requirements.txt >nul 2>&1

where codex >nul 2>&1
if errorlevel 1 (
  echo   Installing the assistant...
  where npm >nul 2>&1
  if not errorlevel 1 npm install -g @openai/codex >nul 2>&1
)
where codex >nul 2>&1
if errorlevel 1 (
  echo   The assistant could not be installed automatically.
  echo   Ask whoever set this up for you to finish it - they'll know what to do.
  pause
  exit /b 1
)

rem Without this nothing is captured, so "My sessions" stays empty.
where entire >nul 2>&1
if errorlevel 1 (
  echo   Setting up session recording...
  rem Scoop is the only documented route on Windows. If it isn't there, carry
  rem on - a missing recorder must never stop someone getting their work done.
  where scoop >nul 2>&1
  if not errorlevel 1 (
    scoop bucket add entire https://github.com/entireio/scoop-bucket.git >nul 2>&1
    scoop install entire/cli >nul 2>&1
  )
)

where entire >nul 2>&1
if not errorlevel 1 (
  if not exist ".entire\settings.json" entire enable --agent codex >nul 2>&1
  if exist ".codex\hooks.json" .venv\Scripts\python.exe scaffold\install_hooks.py >nul 2>&1
)
exit /b 0
