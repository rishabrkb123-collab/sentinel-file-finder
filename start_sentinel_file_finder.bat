@echo off
setlocal
cd /d "%~dp0"

if /i not "%~1"=="hidden" (
    mshta "vbscript:CreateObject(""WScript.Shell"").Run(""cmd /c """"%~f0"""" hidden"",0)(close)"
    exit /b
)

if not exist logs mkdir logs
set "LOG_FILE=%cd%\logs\startup.log"

if exist "dist\SentinelFileFinder\SentinelFileFinder.exe" (
    start "" "dist\SentinelFileFinder\SentinelFileFinder.exe"
    exit /b 0
)

where pythonw >nul 2>nul
if errorlevel 1 (
    > "%LOG_FILE%" echo [ERROR] pythonw.exe was not found in PATH.
    start "" notepad "%LOG_FILE%"
    exit /b 1
)

start "" pythonw app.py
exit /b 0
