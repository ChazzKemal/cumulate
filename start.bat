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

set "PY=%CD%\.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
for /f "delims=" %%i in ('"%PY%" scaffold\tools_index.py --prompt 2^>nul') do set "TOOLS_PROMPT=%%i"

set "PROMPT=You are in the Tool Builder project. Follow AGENTS.md."
if defined FILES set "PROMPT=!PROMPT! Files sitting in the inbox: !FILES! (gitignored, so file search will not find them - read them by path when the time comes)."
if defined TOOLS_PROMPT set "PROMPT=!PROMPT! !TOOLS_PROMPT!"
set "PROMPT=!PROMPT! Greet me in one line, say what is in the inbox if anything, and ask what I need. Do not open, read or profile any file yet - wait until I have told you what I want."

cls
echo.
echo   Tools you already have:
echo.
"%PY%" scaffold\tools_index.py
echo.
echo   Drag a file onto this window, or drop it in the inbox folder.
echo.

codex "!PROMPT!"
