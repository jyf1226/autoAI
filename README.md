# 多领域 GitHub 研究系统（MVP）

这个仓库已经从“单一 games 的 GitHub 游戏项目自动研究系统”升级为“可扩展到多领域的 GitHub 研究系统 MVP”。

当前依然保留一个统一的 `github-watch` 服务，但配置、prompt、规则和数据输出已经按 domain 分层，后续可以继续扩展新的研究领域。

## 当前支持的 domain

- `games`
- `image-processing`
- `short-video`
- `finance`
- `infra`

## 运行前提

- Windows 11
- Docker Desktop（启用 WSL2）
- WSL2 Ubuntu
- 宿主机已安装 Ollama

## 目录结构

```text
.
├─ compose/
├─ config/
│  ├─ repos/
│  ├─ prompts/
│  └─ pipelines.yaml
├─ data/
│  └─ github-watch/
│     ├─ raw/<domain>/
│     ├─ normalized/<domain>/
│     ├─ reports/daily/
│     ├─ reports/weekly/
│     ├─ reports/by-domain/
│     ├─ embeddings/
│     ├─ training-samples/
│     └─ state/
├─ github-watch/
│  └─ app/
│     ├─ exporters/
│     └─ domain_rules/
├─ scripts/
├─ start.ps1
├─ stop.ps1
└─ backup.ps1
```

## GitHub token 放哪

先复制环境文件：

```powershell
Copy-Item .\compose\.env.example .\compose\.env
```

然后编辑 `compose/.env`，至少填写：

- `GITHUB_TOKEN`
- `OLLAMA_BASE_URL` 或 `OLLAMA_HOST`
- `OLLAMA_MODEL`
- `POSTGRES_PASSWORD`
- `N8N_BASIC_AUTH_PASSWORD`

## 宿主机 Ollama 怎么启动

```powershell
ollama serve
ollama list
ollama pull 你在compose\.env里写的模型名
```

## 第一次如何启动整套系统

```powershell
.\start.ps1
```

## 如何只单独运行 github-watch

```powershell
docker compose --env-file .\compose\.env -f .\compose\docker-compose.yml run --rm github-watch python -m app.main
```

生成物重点看这里：

- `data/github-watch/raw/<domain>/`
- `data/github-watch/normalized/<domain>/`
- `data/github-watch/reports/daily/`
- `data/github-watch/reports/by-domain/`
- `data/github-watch/state/`

## 如何新增一个新的 domain

1. 新建 `config/repos/<new-domain>.yaml`
2. 新建 `config/prompts/repo_summary_<new-domain>.md`
3. 在 `github-watch/app/domain_rules/` 增加对应规则文件
4. 如果需要更强输出，可在 exporter 层补该 domain 的特殊导出逻辑

当前实现是轻量 MVP，不需要新增服务，也不需要新增容器。

## 如何每天定时跑

推荐 Windows 任务计划程序，每天执行：

```powershell
docker compose --env-file E:\aiauto\compose\.env -f E:\aiauto\compose\docker-compose.yml run --rm github-watch python -m app.main
```

## 如何迁移到新电脑

1. 安装 Docker Desktop + WSL2 + Ollama
2. 拷贝整个项目目录
3. 还原备份压缩包
4. 重新填写 `compose/.env`
5. 执行 `.\start.ps1`

## 哪些目录最重要必须备份

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

## 当前哪些 exporter 只是预留 stub

- `github-watch/app/exporters/qdrant_exporter.py`
- `github-watch/app/exporters/training_exporter.py`

当前只有 `markdown_exporter.py` 在实际输出链路中生效。

## 容错说明

- 某个 repo 不存在、重命名、权限不足、API 异常时，不会中断整批任务
- Ollama 不可用时，会自动退回基础文本摘要
- 没有 Qdrant / Postgres / Redis，也可以先只验证最小日报链路

## 废弃说明

- 旧的单文件 `config/repos.yaml` 已废弃，改为 `config/repos/*.yaml`
- 旧的 `data/github-watch/raw/*.json` 与 `normalized/*.json` 顶层输出结构已废弃，改为按 domain 分目录
