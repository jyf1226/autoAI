$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$envExample = Join-Path $projectRoot "compose\.env.example"
$envFile = Join-Path $projectRoot "compose\.env"
$composeFile = Join-Path $projectRoot "compose\docker-compose.yml"

Write-Host "检查 Docker Compose 可用性..."
docker compose version | Out-Null

if (-not (Test-Path $envFile)) {
  Write-Host "未发现 compose/.env，自动从 .env.example 复制..."
  Copy-Item $envExample $envFile
}

Write-Host "启动服务..."
docker compose --env-file "$envFile" -f "$composeFile" up -d --build
docker compose --env-file "$envFile" -f "$composeFile" ps

Write-Host ""
Write-Host "访问地址："
Write-Host "  Open WebUI : http://localhost:3000"
Write-Host "  Qdrant     : http://localhost:6333/dashboard"
Write-Host "  n8n        : http://localhost:5678"
Write-Host ""
Write-Host "下一步建议："
Write-Host "  1) 编辑 compose/.env，填入 GITHUB_TOKEN"
Write-Host "  2) 查看 github-watch 日志：docker compose --env-file `"$envFile`" -f `"$composeFile`" logs -f github-watch"
