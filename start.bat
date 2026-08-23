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

rem Also surface anything saved recently - most people never move files.
set "RECENT="
for %%d in ("%USERPROFILE%\Desktop" "%USERPROFILE%\Downloads") do (
  for %%e in (xlsx xls xlsm csv tsv json jsonl log) do (
    for %%f in ("%%~d\*.%%e") do (
      if defined RECENT (set "RECENT=!RECENT!, %%~ff") else (set "RECENT=%%~ff")
    )
  )
)

set "PROMPT=You are in the Tool Builder project. Follow AGENTS.md."
if defined FILES  set "PROMPT=!PROMPT! Files in the inbox: !FILES!."
if defined RECENT set "PROMPT=!PROMPT! Recently saved elsewhere: !RECENT!."
if defined FILES (goto :havefiles)
if defined RECENT (goto :havefiles)
set "PROMPT=!PROMPT! Greet me in one line and ask what I need built. Mention I can drag a file straight onto this window or drop it in the inbox folder."
goto :run
:havefiles
set "PROMPT=!PROMPT! These are gitignored or outside the repo, so file search will not find them - read them directly by path. Profile the most likely one with scaffold/ingest.py, say in plain language what you found, and ask what I need built."
:run
echo.
echo   Tip: you can drag a file onto this window instead of moving it.
echo.
codex "!PROMPT!"
