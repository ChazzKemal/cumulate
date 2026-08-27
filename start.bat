@echo off
setlocal enabledelayedexpansion
rem Double-click this to start. Nothing to install, nothing to type.
rem The code and the person's own work live in different places, so that
rem updating one can never disturb the other. APP is the code; WORKSPACE is
rem theirs. Mirrors start.command.
if not defined CUMULATE_APP set "CUMULATE_APP=%~dp0"
if "%CUMULATE_APP:~-1%"=="\" set "CUMULATE_APP=%CUMULATE_APP:~0,-1%"
if not defined CUMULATE_WORKSPACE set "CUMULATE_WORKSPACE=%CUMULATE_APP%"
set "APP=%CUMULATE_APP%"
cd /d "%CUMULATE_WORKSPACE%"

rem Fresh machine? Get everything in place first.
call "%APP%\scaffold\bootstrap.bat"
if errorlevel 1 exit /b 1
cd /d "%CUMULATE_WORKSPACE%"

rem Shared connection settings ship with the code; personal ones live with the
rem person and override them. eol=# skips comment lines in both files.
if exist "%APP%\config.env" for /f "usebackq eol=# tokens=1,* delims==" %%a in ("%APP%\config.env") do set "%%a=%%b"
if exist ".env" (
  for /f "usebackq eol=# tokens=1,* delims==" %%a in (".env") do set "%%a=%%b"
) else if exist "%APP%\.env" (
  for /f "usebackq eol=# tokens=1,* delims==" %%a in ("%APP%\.env") do set "%%a=%%b"
)

rem Someone needs setting up only if they have no key. Signing in is how a key
rem is issued, so a key already in .env means they are ready - never send them
rem back through the browser for it.
rem Labels cannot live inside a parenthesised block in batch, so this whole
rem stretch runs at top level.
set "NEEDS_SETUP="
if "!OPENAI_API_KEY!"=="" set "NEEDS_SETUP=1"
if not defined NEEDS_SETUP goto ready

echo.
echo   Opening your browser to get you set up...
echo   If nothing opens, go to http://localhost:8501 yourself.
echo.
rem Keep the welcome page's PID, so only it is closed later - never every
rem Streamlit the person happens to have running. headless false is what
rem makes Streamlit open the browser itself.
set "WELCOME_PID="
for /f %%p in ('powershell -NoProfile -Command "(Start-Process -FilePath '%APP%\.venv\Scripts\streamlit.exe' -ArgumentList 'run','%APP%\scaffold\welcome.py','--server.headless','false','--server.port','8501' -WindowStyle Hidden -PassThru).Id"') do set "WELCOME_PID=%%p"
if not defined WELCOME_PID start "" http://localhost:8501
set /a WAITED=0

:waitkey
timeout /t 2 /nobreak >nul
set /a WAITED+=2
if exist .env for /f "usebackq eol=# tokens=1,* delims==" %%a in (".env") do set "%%a=%%b"
rem Delayed expansion: %VAR% would be fixed at parse time and never see the key.
set "NEEDS_SETUP="
if "!OPENAI_API_KEY!"=="" set "NEEDS_SETUP=1"
if not defined NEEDS_SETUP goto gotkey
if !WAITED! LSS 600 goto waitkey

if defined WELCOME_PID taskkill /f /pid !WELCOME_PID! >nul 2>&1
echo   Setup didn't finish. Run this again when you're ready.
pause
exit /b 1

:gotkey
if defined WELCOME_PID taskkill /f /pid !WELCOME_PID! >nul 2>&1

:ready
rem inbox\ is gitignored, so file search can't see it. List it explicitly.
set "FILES="
for %%f in (inbox\*) do (
  if /i not "%%~nxf"==".gitkeep" (
    if defined FILES (set "FILES=!FILES!, inbox/%%~nxf") else (set "FILES=inbox/%%~nxf")
  )
)

set "PY=%APP%\.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
for /f "delims=" %%i in ('""%PY%" "%APP%\scaffold\tools_index.py" --prompt 2^>nul"') do set "TOOLS_PROMPT=%%i"
rem projects\ is gitignored too, for the same reason inbox\ is. Same fix.
rem A blank line is skipped by for /f, so an empty archive leaves this undefined.
for /f "delims=" %%i in ('""%PY%" "%APP%\scaffold\projects_index.py" --prompt 2^>nul"') do set "PROJECTS_PROMPT=%%i"

set "PROMPT=You are in the Tool Builder project. Follow AGENTS.md."
if defined FILES set "PROMPT=!PROMPT! Files sitting in the inbox: !FILES! (gitignored, so file search will not find them - read them by path when the time comes)."
if defined TOOLS_PROMPT set "PROMPT=!PROMPT! !TOOLS_PROMPT!"
if defined PROJECTS_PROMPT set "PROMPT=!PROMPT! !PROJECTS_PROMPT!"
set "PROMPT=!PROMPT! Greet me in one line, say what is in the inbox if anything, and ask what I need. Do not open, read or profile any file yet - wait until I have told you what I want."

cls
echo.
echo   Tools you already have:
echo.
"%PY%" "%APP%\scaffold\tools_index.py"
echo.
echo   Work you did before this existed:
echo.
"%PY%" "%APP%\scaffold\projects_index.py"
echo.
echo   Drag a file onto this window, or drop it in the inbox folder.
echo.

codex "!PROMPT!"
