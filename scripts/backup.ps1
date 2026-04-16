$ErrorActionPreference = "Stop"

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupDir = ".\backups"
$zipPath = Join-Path $backupDir "aiworkflow-data-$timestamp.zip"

if (-not (Test-Path $backupDir)) {
  New-Item -Path $backupDir -ItemType Directory | Out-Null
}

Write-Host "Creating backup from .\data ..."
Compress-Archive -Path ".\data\*" -DestinationPath $zipPath -Force
Write-Host "Backup created: $zipPath"
