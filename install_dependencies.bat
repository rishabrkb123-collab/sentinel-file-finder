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

echo [1/2] Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo.
    echo [ERROR] Failed while upgrading pip.
    echo.
    pause
    exit /b 1
)

echo.
echo [2/2] Installing requirements...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Failed while installing project dependencies.
    echo.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] All dependencies are installed.
echo You can now run start_sentinel_file_finder.bat
echo.
pause
exit /b 0

