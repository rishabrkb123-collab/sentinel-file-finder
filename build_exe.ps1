$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
  python -m venv .venv
}

$venvPython = Join-Path $PWD ".venv\Scripts\python.exe"
$releasePath = Join-Path $PWD "release\SentinelFileFinder"

Get-Process SentinelFileFinder -ErrorAction SilentlyContinue | Stop-Process -Force
if (Test-Path $releasePath) {
  Remove-Item -Recurse -Force $releasePath
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements.txt
& $venvPython -m PyInstaller `
  --noconfirm `
  --clean `
  --name SentinelFileFinder `
  --windowed `
  --distpath "release" `
  --add-data "docs;docs" `
  app.py

Write-Host "Build complete. See release\\SentinelFileFinder\\"
