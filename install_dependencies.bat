@echo off
setlocal
cd /d "%~dp0"
title Sentinel File Finder - Install Dependencies

echo ==========================================
echo Sentinel File Finder Dependency Installer
echo Project: %cd%
echo ==========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found in PATH.
    echo Install Python 3.12+ and rerun this script.
    echo.
    pause
    exit /b 1
)

if not exist ".venv" (
    echo [1/3] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed while creating the virtual environment.
        echo.
        pause
        exit /b 1
    )
)

set "VENV_PYTHON=%cd%\.venv\Scripts\python.exe"

echo [2/3] Upgrading pip...
"%VENV_PYTHON%" -m pip install --upgrade pip
if errorlevel 1 (
    echo.
    echo [ERROR] Failed while upgrading pip.
    echo.
    pause
    exit /b 1
)

echo.
echo [3/3] Installing requirements...
"%VENV_PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Failed while installing project dependencies.
    echo.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] All dependencies are installed.
echo Virtual environment: .venv
echo You can now run start_sentinel_file_finder.bat
echo.
pause
exit /b 0
