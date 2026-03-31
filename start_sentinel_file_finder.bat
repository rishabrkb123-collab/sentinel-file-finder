@echo off
setlocal
cd /d "%~dp0"

if /i not "%~1"=="hidden" (
    where mshta >nul 2>nul
    if errorlevel 1 (
        goto run_visible
    )
    mshta "vbscript:CreateObject(""WScript.Shell"").Run(""cmd /c """"%~f0"""" hidden"",0)(close)"
    exit /b
)

if not exist logs mkdir logs
set "LOG_FILE=%cd%\logs\startup.log"
set "VENV_PYTHONW=%cd%\.venv\Scripts\pythonw.exe"
set "VENV_PYTHON=%cd%\.venv\Scripts\python.exe"

if exist "%VENV_PYTHONW%" (
    start "" "%VENV_PYTHONW%" app.py
    exit /b 0
)

if exist "%VENV_PYTHON%" (
    start "" "%VENV_PYTHON%" app.py
    exit /b 0
)

where pythonw >nul 2>nul
if not errorlevel 1 (
    start "" pythonw app.py
    exit /b 0
)

if exist "release\SentinelFileFinder\SentinelFileFinder.exe" (
    start "" "release\SentinelFileFinder\SentinelFileFinder.exe"
    exit /b 0
)

if exist "dist\SentinelFileFinder\SentinelFileFinder.exe" (
    start "" "dist\SentinelFileFinder\SentinelFileFinder.exe"
    exit /b 0
)

> "%LOG_FILE%" echo [ERROR] No usable launcher was found.
>> "%LOG_FILE%" echo Install dependencies first with install_dependencies.bat or build the executable.
start "" notepad "%LOG_FILE%"
exit /b 1

:run_visible
if exist "%cd%\.venv\Scripts\python.exe" (
    start "" "%cd%\.venv\Scripts\python.exe" app.py
    exit /b 0
)
if exist "release\SentinelFileFinder\SentinelFileFinder.exe" (
    start "" "release\SentinelFileFinder\SentinelFileFinder.exe"
    exit /b 0
)
if exist "dist\SentinelFileFinder\SentinelFileFinder.exe" (
    start "" "dist\SentinelFileFinder\SentinelFileFinder.exe"
    exit /b 0
)
echo [ERROR] Could not start Sentinel File Finder.
echo Run install_dependencies.bat first.
pause
exit /b 1
