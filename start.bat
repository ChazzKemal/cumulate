@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

if exist .env (for /f "usebackq tokens=1,* delims==" %%a in (".env") do set "%%a=%%b")
if "%OPENAI_API_KEY%"=="" (
  echo.
  echo   One-time setup needed.
  echo.
  echo   Open .env.example in this folder, paste your OpenAI key in,
  echo   and save it as .env  Then run this again.
  echo.
  pause
  exit /b 1
)

rem inbox\ is gitignored, so file search can't see it. List it explicitly.
set "FILES="
for %%f in (inbox\*) do (
  if /i not "%%~nxf"==".gitkeep" (
    if defined FILES (set "FILES=!FILES!, inbox/%%~nxf") else (set "FILES=inbox/%%~nxf")
  )
)

if defined FILES (
  set "PROMPT=Files waiting in the inbox: !FILES!. These are gitignored so file search will not find them - read them directly by path. Profile the first one with scaffold/ingest.py, tell me in plain language what you found, and ask what I need built."
) else (
  set "PROMPT=The inbox is empty. Greet me in one line and ask what I need built, and mention they can drop a spreadsheet into the inbox folder."
)

cls
codex "!PROMPT!"
