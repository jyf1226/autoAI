# Compose 目录说明

本目录是整个 MVP 的容器编排入口。

## 当前包含服务

- open-webui
- qdrant
- postgres
- redis
- n8n
- github-watch

## 关键约束

- Ollama 必须运行在宿主机，不在容器中。
- 所有持久化数据通过 bind mount 统一落到 `../data`。
- 配置使用 `.env`，不写死绝对路径。
- AnythingLLM 暂不加入，仅在后续扩展时接入。

## 常用命令

```powershell
docker compose --env-file .\compose\.env -f .\compose\docker-compose.yml up -d --build
docker compose --env-file .\compose\.env -f .\compose\docker-compose.yml ps
docker compose --env-file .\compose\.env -f .\compose\docker-compose.yml logs -f github-watch
```
