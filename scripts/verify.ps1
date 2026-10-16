param([int]$AfterProcessId = 0)
$ErrorActionPreference = 'Stop'
$verificationRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $verificationRoot
$verificationPython = Join-Path $verificationRoot '.venv/Scripts/python.exe'
$verificationReport = Join-Path $verificationRoot 'artifacts/benchmark-v2.json'
$verificationStatus = Join-Path $verificationRoot 'artifacts/verification-status.json'

function Publish-BenchmarkReport {
  if (Test-Path -LiteralPath $verificationReport) {
    & $verificationPython scripts/report_benchmark.py
    if ($LASTEXITCODE -ne 0) { throw 'Nie udalo sie przygotowac raportu.' }
    Copy-Item -LiteralPath $verificationReport -Destination (Join-Path $verificationRoot 'docs/benchmark-v2-data.json') -Force
  }
}

if ($AfterProcessId -gt 0) {
  $verificationProcess = Get-Process -Id $AfterProcessId -ErrorAction SilentlyContinue
  $verificationRevision = ''
  while ($verificationProcess -and !$verificationProcess.HasExited) {
    if (Test-Path -LiteralPath $verificationReport) {
      $verificationModified = (Get-Item -LiteralPath $verificationReport).LastWriteTimeUtc.ToString('O')
      if ($verificationModified -ne $verificationRevision) {
        Publish-BenchmarkReport
        $verificationRevision = $verificationModified
        $verificationProgress = Get-Content -LiteralPath $verificationReport -Raw | ConvertFrom-Json
        @{ running=$true; stage='native'; nativeMatrixComplete=$false;
           pythonPassed=$null; buildPassed=$null; browserPassed=$null;
           completedRuns=$verificationProgress.runs.Count; measuredProfiles=$verificationProgress.summaries.Count;
           updatedAt=[DateTimeOffset]::Now.ToString('O') } | ConvertTo-Json | Set-Content -LiteralPath $verificationStatus -Encoding utf8
        Write-Host ('Natywny benchmark: {0}/60 poprawnych prob.' -f $verificationProgress.runs.Count)
      }
    }
    Start-Sleep -Seconds 5
    $verificationProcess.Refresh()
  }
} else {
  & $verificationPython scripts/benchmark.py
  if ($LASTEXITCODE -ne 0) { Publish-BenchmarkReport; throw 'Benchmark przerwany; zachowano ukonczone proby.' }
}

Publish-BenchmarkReport
$verificationData = Get-Content -LiteralPath $verificationReport -Raw | ConvertFrom-Json
$verificationComplete = $true
$verificationCases = @(@{scene='burner';duration=2},@{scene='candle';duration=2},@{scene='burner';duration=6},@{scene='candle';duration=6},@{scene='wood';duration=15})
foreach ($verificationCase in $verificationCases) {
  foreach ($verificationMode in @('openmp','mpi2','mpi4')) {
    foreach ($verificationIteration in 0..3) {
      $verificationMatches = @($verificationData.runs | Where-Object {
        $_.config.scene -eq $verificationCase.scene -and $_.config.duration -eq $verificationCase.duration -and
        $_.config.quality -eq 'preview' -and $_.profile.mode -eq $verificationMode -and
        $_.iteration -eq $verificationIteration -and $_.nativeExact -eq $true -and $_.preview -eq $true
      })
      if ($verificationMatches.Count -eq 0) { $verificationComplete = $false }
    }
    $verificationSummaries = @($verificationData.summaries | Where-Object {
      $_.config.scene -eq $verificationCase.scene -and $_.config.duration -eq $verificationCase.duration -and
      $_.config.quality -eq 'preview' -and $_.mode -eq $verificationMode -and $_.comparisons.Count -ge 3
    })
    if ($verificationSummaries.Count -eq 0) { $verificationComplete = $false }
  }
}
& $verificationPython -m pytest tests -q *> artifacts/pytest-v2.log
$verificationPythonPassed = $LASTEXITCODE -eq 0
& npm.cmd run build *> artifacts/build-v2.log
$verificationBuildPassed = $LASTEXITCODE -eq 0
# Playwright uses the running local server on port 8765.
& npm.cmd run test:e2e *> artifacts/e2e-v2.log
$verificationBrowserPassed = $LASTEXITCODE -eq 0
@{ running=$false; stage=$(if ($verificationComplete -and $verificationPythonPassed -and $verificationBuildPassed -and $verificationBrowserPassed) {'completed'} else {'failed'});
   nativeMatrixComplete=$verificationComplete; pythonPassed=$verificationPythonPassed;
   buildPassed=$verificationBuildPassed; browserPassed=$verificationBrowserPassed;
   completedRuns=$verificationData.runs.Count; measuredProfiles=$verificationData.summaries.Count;
   completedAt=[DateTimeOffset]::Now.ToString('O') } | ConvertTo-Json | Set-Content -LiteralPath $verificationStatus -Encoding utf8
if (!$verificationComplete -or !$verificationPythonPassed -or !$verificationBuildPassed -or !$verificationBrowserPassed) {
  throw 'Weryfikacja niekompletna lub nieudana. Sprawdz artifacts/verification-status.json i logi.'
}
Write-Host 'Weryfikacja zakonczona. Raport: docs/benchmark-v2.md. FAIL bramki MPI oznacza zachowanie OpenMP.'
