param([switch]$NativeCampaign, [double]$Hours = 8, [double]$GiB = 4)
$ErrorActionPreference = 'Stop'
$verificationRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $verificationRoot
New-Item -ItemType Directory -Path (Join-Path $verificationRoot 'artifacts') -Force | Out-Null
$verificationPython = Join-Path $verificationRoot '.venv/Scripts/python.exe'
& $verificationPython -m pytest tests -q *> artifacts/pytest-v3.log
$pythonPassed = $LASTEXITCODE -eq 0
& npm.cmd run build *> artifacts/build-v3.log
$buildPassed = $LASTEXITCODE -eq 0
& npm.cmd run test:e2e *> artifacts/e2e-v3.log
$browserPassed = $LASTEXITCODE -eq 0
if ($pythonPassed -and $buildPassed -and $browserPassed -and $NativeCampaign) {
    & $verificationPython scripts/campaign_v3.py --hours $Hours --gib $GiB
    if ($LASTEXITCODE -ne 0) { throw 'Kampania przerwana. Zachowano pomiary i dziennik.' }
}
$campaignPath = Join-Path $verificationRoot 'artifacts/campaign-v3/campaign.json'
$campaign = if (Test-Path -LiteralPath $campaignPath) { Get-Content -LiteralPath $campaignPath -Raw | ConvertFrom-Json } else { $null }
@{ pythonPassed=$pythonPassed; buildPassed=$buildPassed; browserPassed=$browserPassed;
   completedNativeRuns=$(if ($campaign) { $campaign.runs.Count } else { 0 });
   nativeCampaignStatus=$(if ($campaign) { $campaign.status } else { 'not-run' });
   qualificationPolicy=(Get-Content -LiteralPath config/validation-v3.json -Raw | ConvertFrom-Json).status;
   completedAt=[DateTimeOffset]::Now.ToString('O') } | ConvertTo-Json | Set-Content -LiteralPath artifacts/verification-status-v3.json -Encoding utf8
if (!$pythonPassed -or !$buildPassed -or !$browserPassed) { throw 'Testy nie przeszly. Sprawdz artifacts/*-v3.log.' }
Write-Host 'Testy aplikacji zakonczone. Status badan numerycznych jest raportowany osobno.'
