# Compose 目录说明

这里是多领域 GitHub 研究系统的容器编排入口。

## 当前服务

- `open-webui`
- `qdrant`
- `postgres`
- `redis`
- `n8n`
- `github-watch`

## 关键约束

- Ollama 运行在宿主机，不进容器。
- 所有持久化目录统一 bind mount 到 `../data`。
- `github-watch` 可以在没有 Qdrant / Postgres / Redis 的情况下先产出最小日报。
- AnythingLLM 当前不加入服务，只在后续扩展时复用同一数据和网络策略。

## 常用命令

```powershell
docker compose --env-file .\compose\.env -f .\compose\docker-compose.yml up -d --build
docker compose --env-file .\compose\.env -f .\compose\docker-compose.yml ps
docker compose --env-file .\compose\.env -f .\compose\docker-compose.yml run --rm github-watch python -m app.main
docker compose --env-file .\compose\.env -f .\compose\docker-compose.yml logs -f github-watch
```
