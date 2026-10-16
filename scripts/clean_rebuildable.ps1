param([switch]$Apply, [string]$Root = 'C:/Users/Tront/source/repos')
$ErrorActionPreference = 'Stop'
$cleanupRoot = (Resolve-Path -LiteralPath $Root).Path.TrimEnd('\','/')
$protectedRoot = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$commands = @(Get-CimInstance Win32_Process | ForEach-Object { $_.CommandLine } | Where-Object { $_ })
$before = (Get-PSDrive C).Free
$records = @()
$queue = [Collections.Generic.Stack[string]]::new()
Get-ChildItem -LiteralPath $cleanupRoot -Directory | Where-Object { $_.FullName -ne $protectedRoot } | ForEach-Object { $queue.Push($_.FullName) }
while ($queue.Count) {
  $directory = Get-Item -LiteralPath $queue.Pop() -Force
  if ($directory.Attributes -band [IO.FileAttributes]::ReparsePoint) { continue }
  if ($directory.Name -eq '.git') { continue }
  if ($directory.Name -notin @('node_modules','bin','obj','.next','dist','build')) {
    Get-ChildItem -LiteralPath $directory.FullName -Directory -Force -ErrorAction SilentlyContinue | ForEach-Object { $queue.Push($_.FullName) }
    continue
  }
  $target = $directory.FullName
  $reason = $null
  $parent = $directory.Parent.FullName
  $manifest = $parent
  while ($manifest -and $manifest.StartsWith($cleanupRoot,[StringComparison]::OrdinalIgnoreCase) -and !(Test-Path -LiteralPath (Join-Path $manifest 'package.json'))) { $manifest = Split-Path -Parent $manifest }
  $isDotnet = @(Get-ChildItem -LiteralPath $parent -Filter '*.csproj' -File -ErrorAction SilentlyContinue).Count -gt 0
  $hasManifest = $manifest -and $manifest.StartsWith($cleanupRoot,[StringComparison]::OrdinalIgnoreCase) -and (Test-Path -LiteralPath (Join-Path $manifest 'package.json'))
  if (!$hasManifest -and !$isDotnet) { $reason = 'no reconstruction manifest' }
  if ($commands | Where-Object { $_.IndexOf($target,[StringComparison]::OrdinalIgnoreCase) -ge 0 }) { $reason = 'active process' }
  $repository = & git -C $parent rev-parse --show-toplevel 2>$null
  if ($LASTEXITCODE -eq 0) {
    $relative = [IO.Path]::GetRelativePath($repository,$target).Replace('\','/')
    $tracked = @(& git -C $repository ls-files -- $relative)
    if ($tracked.Count) { $reason = 'tracked files' }
  }
  $children = @(Get-ChildItem -LiteralPath $target -Recurse -Force -ErrorAction SilentlyContinue)
  if ($children | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }) { $reason = 'nested reparse point' }
  if ($directory.Name -in @('bin','obj') -and ($children | Where-Object { $_.Extension -in @('.db','.sqlite','.sqlite3') })) { $reason = 'possible persistent database' }
  $bytes = ($children | Where-Object { !$_.PSIsContainer } | Measure-Object -Property Length -Sum).Sum
  $state = if ($reason) {'skipped'} elseif ($Apply) {'removed'} else {'eligible'}
  if ($Apply -and !$reason) {
    $resolved = (Resolve-Path -LiteralPath $target).Path
    if (!$resolved.StartsWith($cleanupRoot + '\',[StringComparison]::OrdinalIgnoreCase) -or $resolved.StartsWith($protectedRoot,[StringComparison]::OrdinalIgnoreCase) -or $resolved -ne $target) { throw "Unsafe cleanup target: $resolved" }
    try { Remove-Item -LiteralPath $resolved -Recurse -Force }
    catch { $state='partial';$reason=$_.Exception.Message }
  }
  $records += @{path=$target;bytes=$bytes;status=$state;reason=$reason}
}
$report = @{apply=[bool]$Apply;root=$cleanupRoot;reclaimedBytes=($before - (Get-PSDrive C).Free)*-1;records=$records;time=[DateTimeOffset]::Now.ToString('O')}
$output = Join-Path $protectedRoot 'artifacts/cleanup-v3.json'
$report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $output -Encoding utf8
$report | ConvertTo-Json -Depth 5
