$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$envFile = Join-Path $projectRoot "compose\.env"
$composeFile = Join-Path $projectRoot "compose\docker-compose.yml"

Write-Host "停止服务..."
docker compose --env-file "$envFile" -f "$composeFile" down
Write-Host "已停止。"
