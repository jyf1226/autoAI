# Compose 使用说明

本目录提供 Windows + Docker Desktop + WSL2 的本地 AI 工作流编排。

## 服务清单

- open-webui
- qdrant
- postgres
- redis
- n8n
- github-watch

> 说明：Ollama 运行在宿主机，不在容器中。

## 启动前准备

1. 安装并启动 Docker Desktop（启用 WSL2）。
2. 在宿主机安装并启动 Ollama，确认 `http://localhost:11434` 可访问。
3. 复制环境变量模板：

```powershell
Copy-Item .\compose\.env.example .\compose\.env
```

4. 编辑 `compose/.env`，至少修改：
   - `POSTGRES_PASSWORD`
   - `N8N_BASIC_AUTH_PASSWORD`
   - `GITHUB_TOKEN`

## 第一天启动命令

在项目根目录执行：

```powershell
docker compose --env-file .\compose\.env -f .\compose\docker-compose.yml up -d --build
docker compose --env-file .\compose\.env -f .\compose\docker-compose.yml ps
```

## 访问入口

- Open WebUI: `http://localhost:3000`
- Qdrant: `http://localhost:6333/dashboard`
- n8n: `http://localhost:5678`

## Ollama 连接说明（Open WebUI）

- `OLLAMA_BASE_URL` 默认配置为 `http://host.docker.internal:11434`
- 该配置适配 Docker Desktop 的 Windows + WSL2 场景
- 如你使用其他网络拓扑，可在 `.env` 覆盖该值

## 预留 AnythingLLM

当前未启用 AnythingLLM。后续可在本文件同级 `docker-compose.yml` 增加 `anythingllm` 服务，并复用：
- `../data/` 持久化策略
- `ai-net` 网络
- `OLLAMA_BASE_URL` 宿主机连接方式
