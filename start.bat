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

set "PROMPT=You are in the Tool Builder project. Follow AGENTS.md."
if defined FILES set "PROMPT=!PROMPT! Files sitting in the inbox: !FILES! (gitignored, so file search will not find them - read them by path when the time comes)."
set "PROMPT=!PROMPT! Greet me in one line, say what is in the inbox if anything, and ask what I need. Do not open, read or profile any file yet - wait until I have told you what I want."

:run
:havefiles
set "PROMPT=!PROMPT! The inbox is gitignored, so file search will not find these - read them directly by path. Profile the most likely one with scaffold/ingest.py, say in plain language what you found, and ask what I need built."
:run
echo.
echo   Tip: you can drag a file onto this window instead of moving it.
echo.
codex "!PROMPT!"
