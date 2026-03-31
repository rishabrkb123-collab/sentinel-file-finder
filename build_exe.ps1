$ErrorActionPreference = "Stop"

python -m pip install -r requirements.txt
python -m PyInstaller `
  --noconfirm `
  --clean `
  --name SentinelFileFinder `
  --windowed `
  app.py

Write-Host "Build complete. See dist\\SentinelFileFinder\\"
