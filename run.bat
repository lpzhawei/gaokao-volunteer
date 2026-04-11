@echo off
cd /d "%~dp0"

if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe main.py
) else if exist ..\venv\Scripts\python.exe (
    ..\venv\Scripts\python.exe main.py
) else (
    echo [ERROR] venv not found. Please run setup.bat first.
    pause
)
