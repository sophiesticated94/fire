$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if (!(Test-Path -LiteralPath '.venv/Scripts/python.exe')) { python -m venv .venv }
& ./.venv/Scripts/python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Nie udalo sie zainstalowac bibliotek Python.' }
& npm.cmd ci
if ($LASTEXITCODE -ne 0) { throw 'Nie udalo sie zainstalowac bibliotek interfejsu.' }
$solverFile = Join-Path $projectRoot 'tools/fds/firemodels/FDS6/bin/fds_openmp.exe'
if (!(Test-Path -LiteralPath $solverFile)) {
  New-Item -ItemType Directory -Force tools | Out-Null
  $installerFile = Join-Path $projectRoot 'tools/fds-installer.exe'
  if (!(Test-Path -LiteralPath $installerFile)) {
    Invoke-WebRequest 'https://github.com/firemodels/fds/releases/download/FDS-6.11.1/FDS-6.11.1_SMV-6.11.2_win.exe' -OutFile $installerFile
  }
  $expectedHash = '302EC837CAAEA8CB990CECE085BEE2284A0338D64FAC0B77D46749A92AB12DFC'
  if ((Get-FileHash -LiteralPath $installerFile -Algorithm SHA256).Hash -ne $expectedHash) { throw 'Niezgodna suma SHA256 archiwum FDS.' }
  # Official self-extracting archive; extract locally without running its setup.
  & ./.venv/Scripts/python.exe -c 'import zipfile; zipfile.ZipFile("tools/fds-installer.exe").extractall("tools/fds")'
  if ($LASTEXITCODE -ne 0) { throw 'Nie udalo sie rozpakowac FDS.' }
}
& npm.cmd run build
if ($LASTEXITCODE -ne 0) { throw 'Kompilacja nie powiodla sie.' }
Write-Host 'Gotowe. Uruchom .\start.ps1'
