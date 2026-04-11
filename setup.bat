@echo off
cd /d "%~dp0"

echo ============================================
echo   Hebei Gaokao Volunteer System - Setup
echo ============================================
echo.

where python > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+
    echo Download: https://www.python.org/downloads/
    echo Remember to check "Add Python to PATH"
    pause
    exit /b 1
)

echo [1/3] Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create venv
    pause
    exit /b 1
)

echo [2/3] Installing dependencies (may take a few minutes)...
venv\Scripts\pip.exe install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo [3/3] Done!
echo.
echo Now double-click "run.bat" to start the program
echo.
pause
