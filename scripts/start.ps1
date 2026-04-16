$ErrorActionPreference = "Stop"

Write-Host "Starting local AI workflow services..."
docker compose --env-file ".\compose\.env" -f ".\compose\docker-compose.yml" up -d --build
docker compose --env-file ".\compose\.env" -f ".\compose\docker-compose.yml" ps
Write-Host "Done."
