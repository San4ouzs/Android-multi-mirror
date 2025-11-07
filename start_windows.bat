@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python not found. Please install Python 3.10+ and re-run.
  pause
  exit /b 1
)
python -m pip install -r requirements.txt
python multi_mirror.py
