@echo off
title Urban Forest Diwali Party Pass Portal
cd /d "%~dp0"
echo ========================================================
echo Starting Urban Forest Diwali Pass Portal...
echo ========================================================
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python run.py
) else (
    python run.py
)
pause
