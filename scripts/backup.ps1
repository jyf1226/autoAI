$ErrorActionPreference = "Stop"

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$backupDir = Join-Path $projectRoot "backups"
$zipPath = Join-Path $backupDir "github-research-system-backup-$timestamp.zip"
$stageDir = Join-Path $backupDir "stage-$timestamp"

if (-not (Test-Path $backupDir)) {
  New-Item -Path $backupDir -ItemType Directory | Out-Null
}

New-Item -Path $stageDir -ItemType Directory | Out-Null

$items = @(
  "compose",
  "config",
  "data\github-watch",
  "data\openwebui",
  "data\qdrant",
  "data\postgres",
  "data\redis",
  "data\n8n"
)

foreach ($item in $items) {
  $source = Join-Path $projectRoot $item
  if (Test-Path $source) {
    $target = Join-Path $stageDir $item
    New-Item -Path (Split-Path $target -Parent) -ItemType Directory -Force | Out-Null
    Copy-Item -Path $source -Destination $target -Recurse -Force
  }
}

Compress-Archive -Path (Join-Path $stageDir "*") -DestinationPath $zipPath -Force
Remove-Item $stageDir -Recurse -Force
Write-Host "备份已生成: $zipPath"
