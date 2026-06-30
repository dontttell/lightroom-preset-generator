@echo off
cd /d "%~dp0"

set "PY=%~dp0venv\Scripts\python.exe"

echo ========================================
echo   Lightroom Preset Learner  UI v1.6
echo   Dir: %CD%
echo ========================================

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+
    pause
    exit /b 1
)

if not exist "%PY%" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create venv
        pause
        exit /b 1
    )
    "%PY%" -m pip install --upgrade pip
    "%PY%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

if exist "gui\__pycache__" rd /s /q "gui\__pycache__"

echo.
echo Checking UI version...
"%PY%" scripts\verify_ui.py
if errorlevel 1 (
    echo ERROR: UI version check failed
    pause
    exit /b 1
)

echo.
echo Starting app...
"%PY%" -B main.py
if errorlevel 1 pause
