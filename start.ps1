param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if (!(Test-Path -LiteralPath '.venv/Scripts/python.exe') -or !(Test-Path -LiteralPath 'node_modules')) {
  throw 'Najpierw uruchom .\scripts\setup.ps1'
}
& npm.cmd run build
if ($LASTEXITCODE -ne 0) { throw 'Kompilacja nie powiodla sie.' }
if (!$NoBrowser) {
  Start-Process -FilePath 'powershell.exe' -ArgumentList '-NoProfile','-Command','Start-Sleep -Seconds 3; Start-Process http://127.0.0.1:8765' -WindowStyle Hidden
}
Write-Host 'IGNIS: http://127.0.0.1:8765 — Ctrl+C zatrzymuje serwer.'
& ./.venv/Scripts/python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8765
