# Compatibility entry point. Historical v2 evidence must never certify v3 runs.
param([int]$AfterProcessId = 0)
$ErrorActionPreference = 'Stop'
Write-Warning 'Raporty v2 sa historyczne. Przekierowanie do weryfikacji v3.'
if ($AfterProcessId -gt 0) {
    while (Get-Process -Id $AfterProcessId -ErrorAction SilentlyContinue) { Start-Sleep -Seconds 5 }
}
& (Join-Path $PSScriptRoot 'verify_v3.ps1')
