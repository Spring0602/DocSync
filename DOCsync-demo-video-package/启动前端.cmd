@echo off
setlocal
title DocSync local preview
python "%~dp0..\scripts\serve_frontend.py"
if errorlevel 1 (
  echo.
  echo Could not start DocSync. Install Python 3.12 or newer and add it to PATH.
  echo Keep the complete project folders together, then try again.
  pause
)
endlocal
