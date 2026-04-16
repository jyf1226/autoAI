$ErrorActionPreference = "Stop"

Write-Host "Stopping local AI workflow services..."
docker compose --env-file ".\compose\.env" -f ".\compose\docker-compose.yml" down
Write-Host "Done."
