@echo off
rem Double-click to install Cumulate. Per-user, no admin rights, nothing to
rem install first. Fetches the latest install.ps1 from GitHub and runs it with a
rem process-scoped policy bypass, so no execution policy is ever changed.
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor 3072; irm https://raw.githubusercontent.com/ChazzKemal/cumulate/master/install.ps1 | iex"
pause
