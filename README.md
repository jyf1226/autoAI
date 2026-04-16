# 本地 AI 工作流（Windows + WSL2 + Docker Compose）

## 项目结构

```text
.
├─ compose/
├─ data/
├─ github-watch/
└─ scripts/
```

## 第一天启动（按顺序）

```powershell
Copy-Item .\compose\.env.example .\compose\.env
# 编辑 .\compose\.env，填写 GITHUB_TOKEN 和密码
.\scripts\start.ps1
```

## 最小可运行示例

1. `compose/.env` 中填入可用的 `GITHUB_TOKEN`
2. 保持 `github-watch/config/repos.yaml` 默认仓库
3. 运行：

```powershell
docker compose --env-file .\compose\.env -f .\compose\docker-compose.yml up -d --build github-watch
docker compose --env-file .\compose\.env -f .\compose\docker-compose.yml logs -f github-watch
```

若成功，`data/github-watch/reports/` 会出现当天 Markdown 报告。

## 迁移到新电脑步骤

1. 安装 Docker Desktop（启用 WSL2）和 Ollama
2. 复制整个项目目录到新电脑
3. 在项目根目录执行：

```powershell
Copy-Item .\compose\.env.example .\compose\.env
# 填写新环境密钥
.\scripts\start.ps1
```

4. 验证服务状态：

```powershell
docker compose --env-file .\compose\.env -f .\compose\docker-compose.yml ps
```

## 说明

- 所有持久化都在 `./data`（bind mount）
- Ollama 通过 `host.docker.internal:11434` 从容器访问宿主机
- 预留了后续接入 AnythingLLM 的空间，当前未启用
