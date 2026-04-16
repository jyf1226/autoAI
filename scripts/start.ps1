$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$envExample = Join-Path $projectRoot "compose\.env.example"
$envFile = Join-Path $projectRoot "compose\.env"
$composeFile = Join-Path $projectRoot "compose\docker-compose.yml"

Write-Host "Checking docker compose..."
docker compose version | Out-Null

if (-not (Test-Path $envFile)) {
  Write-Host "compose/.env not found, copying from .env.example"
  Copy-Item $envExample $envFile
}

Write-Host "Starting services..."
docker compose --env-file "$envFile" -f "$composeFile" up -d --build
docker compose --env-file "$envFile" -f "$composeFile" ps

Write-Host ""
Write-Host "URLs:"
Write-Host "  Open WebUI : http://localhost:3000"
Write-Host "  Qdrant     : http://localhost:6333/dashboard"
Write-Host "  n8n        : http://localhost:5678"
Write-Host ""
Write-Host "Next:"
Write-Host "  - Edit compose/.env and set GITHUB_TOKEN"
Write-Host "  - Tail logs: docker compose --env-file compose/.env -f compose/docker-compose.yml logs -f github-watch"
