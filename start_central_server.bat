@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 central_server.py
) else (
  python central_server.py
)
if errorlevel 1 (
  echo.
  echo PlantPulse Central Server could not start.
  echo Check Python 3 installation and whether port 8770 is already in use.
  pause
)
