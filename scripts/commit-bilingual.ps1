param(
  [Parameter(Mandatory = $true)]
  [string]$SubjectZh,
  [Parameter(Mandatory = $true)]
  [string]$SubjectEn,
  [Parameter(Mandatory = $true)]
  [string]$BodyZh,
  [Parameter(Mandatory = $true)]
  [string]$BodyEn
)

$ErrorActionPreference = "Stop"

# Force UTF-8 pipeline/output to prevent Chinese commit message corruption.
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONIOENCODING = "utf-8"

$message = @"
$SubjectZh / $SubjectEn

$BodyZh
$BodyEn
"@

$tempFile = Join-Path $env:TEMP "git-commit-message-utf8.txt"
[System.IO.File]::WriteAllText($tempFile, $message, [System.Text.UTF8Encoding]::new($false))

git commit -F $tempFile
Remove-Item $tempFile -ErrorAction SilentlyContinue
