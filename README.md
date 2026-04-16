# GitHub 游戏项目自动研究系统（MVP）

本项目用于在本地自动跟踪指定 GitHub 游戏仓库，抓取最近更新，生成中文日报，并为后续接入知识库 / Qdrant / 训练样本流程预留接口。

## 运行前提

- Windows 11
- Docker Desktop（启用 WSL2）
- WSL2 Ubuntu
- 宿主机已安装 Ollama

## 目录结构

```text
.
├─ compose/
│  ├─ docker-compose.yml
│  ├─ .env.example
│  └─ README.md
├─ config/
│  └─ repos.yaml
├─ data/
│  ├─ openwebui/
│  ├─ qdrant/
│  ├─ postgres/
│  ├─ redis/
│  ├─ n8n/
│  └─ github-watch/
│     ├─ raw/
│     ├─ normalized/
│     ├─ reports/
│     └─ state/
├─ github-watch/
│  ├─ app/
│  ├─ requirements.txt
│  ├─ Dockerfile
│  └─ README.md
├─ scripts/
│  ├─ start.ps1
│  ├─ stop.ps1
│  └─ backup.ps1
├─ start.ps1
├─ stop.ps1
└─ backup.ps1
```

## GitHub Token 配置

1. 复制环境文件：

```powershell
Copy-Item .\compose\.env.example .\compose\.env
```

2. 编辑 `compose/.env`，至少修改：
   - `GITHUB_TOKEN`
   - `POSTGRES_PASSWORD`
   - `N8N_BASIC_AUTH_PASSWORD`

## 宿主机 Ollama 启动

```powershell
ollama serve
```

可选拉模型：

```powershell
ollama pull qwen2.5-coder:14b-instruct-q4_K_M
```

## 第一次启动整套系统

```powershell
.\start.ps1
```

## 只单独运行 github-watch

```powershell
docker compose --env-file .\compose\.env -f .\compose\docker-compose.yml up -d --build github-watch
docker compose --env-file .\compose\.env -f .\compose\docker-compose.yml logs -f github-watch
```

说明：即使 Ollama 不可用，`github-watch` 也会降级输出基础文本摘要；即使暂时不使用 Qdrant，也不影响 `github-watch` 最小流程产出日报。

## 每天定时跑

推荐 Windows 任务计划程序，每天执行：

```powershell
powershell -ExecutionPolicy Bypass -File E:\aiauto\start.ps1
```

如果你只想跑抓取，不希望常驻，可在任务计划中执行：

```powershell
docker compose --env-file E:\aiauto\compose\.env -f E:\aiauto\compose\docker-compose.yml run --rm github-watch python -m app.main
```

## 迁移到新机器

1. 安装 Docker Desktop + WSL2 + Ollama
2. 拷贝整个项目目录
3. 恢复备份包（见下节）
4. 重新填写新机器的 `compose/.env`
5. 执行 `.\start.ps1`

## 备份与必须保留目录

强烈建议至少备份：

- `compose/`
- `config/`
- `data/github-watch/`
- `data/openwebui/`
- `data/qdrant/`
- `data/postgres/`
- `data/redis/`
- `data/n8n/`

一键备份：

```powershell
.\backup.ps1
```

## 关于异常仓库

如果某个仓库不存在、私有、或 API 异常，`github-watch` 会在日志和报告中记录错误，但不会中断整批任务。
