@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

rem Fresh machine? Get everything in place first.
call scaffold\bootstrap.bat
if errorlevel 1 exit /b 1

if exist .env (for /f "usebackq tokens=1,* delims==" %%a in (".env") do set "%%a=%%b")
rem Labels cannot live inside a parenthesised block in batch, so this runs at
rem top level: skip ahead when a key is already there, otherwise sign in.
if not "%OPENAI_API_KEY%"=="" goto haskey

echo.
echo   Opening your browser to get you set up...
echo.
start "" /b .venv\Scripts\streamlit.exe run scaffold\welcome.py --server.port 8501
set /a WAITED=0

:waitkey
timeout /t 2 /nobreak >nul
set /a WAITED+=2
if exist .env (for /f "usebackq tokens=1,* delims==" %%a in (".env") do set "%%a=%%b")
rem Delayed expansion: %VAR% would be fixed at parse time and never see the key.
if not "!OPENAI_API_KEY!"=="" goto gotkey
if !WAITED! LSS 600 goto waitkey

echo   Setup didn't finish. Run this again when you're ready.
pause
exit /b 1

:gotkey
taskkill /f /im streamlit.exe >nul 2>&1

:haskey

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
rem projects\ is gitignored too, for the same reason inbox\ is. Same fix.
rem A blank line is skipped by for /f, so an empty archive leaves this undefined.
for /f "delims=" %%i in ('"%PY%" scaffold\projects_index.py --prompt 2^>nul') do set "PROJECTS_PROMPT=%%i"

set "PROMPT=You are in the Tool Builder project. Follow AGENTS.md."
if defined FILES set "PROMPT=!PROMPT! Files sitting in the inbox: !FILES! (gitignored, so file search will not find them - read them by path when the time comes)."
if defined TOOLS_PROMPT set "PROMPT=!PROMPT! !TOOLS_PROMPT!"
if defined PROJECTS_PROMPT set "PROMPT=!PROMPT! !PROJECTS_PROMPT!"
set "PROMPT=!PROMPT! Greet me in one line, say what is in the inbox if anything, and ask what I need. Do not open, read or profile any file yet - wait until I have told you what I want."

cls
echo.
echo   Tools you already have:
echo.
"%PY%" scaffold\tools_index.py
echo.
echo   Work you did before this existed:
echo.
"%PY%" scaffold\projects_index.py
echo.
echo   Drag a file onto this window, or drop it in the inbox folder.
echo.

codex "!PROMPT!"
