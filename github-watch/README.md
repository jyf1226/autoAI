# github-watch

`github-watch` 仍然是唯一的抓取与研究服务，但现在已升级为多领域 MVP。

## 当前支持的 domain

- `games`
- `image-processing`
- `short-video`
- `finance`
- `infra`

## 当前处理流程

1. 读取 `config/repos/*.yaml`
2. 为每个 domain / group / repo 计算抓取窗口
3. 拉取 commits / pull requests / issues
4. 原始 JSON 按 domain 写入 `data/github-watch/raw/<domain>/`
5. 规范化 JSON 按 domain 写入 `data/github-watch/normalized/<domain>/`
6. 按 domain 读取 `config/ollama_models.yaml` 自动选择 Ollama 模型，并加载 `config/prompts/*.md`
7. 输出全局日报到 `reports/daily/`
8. 输出按 domain 日报到 `reports/by-domain/`
9. 预留 embeddings / training-samples exporter

## exporter 状态

- `markdown_exporter.py`: 实际使用
- `qdrant_exporter.py`: **stub**，只建目录+日志，不写远端 Qdrant
- `training_exporter.py`: **stub**，只确保 `placeholder.jsonl` 存在

## 容错策略

- 单仓库失败不影响整批任务
- 仓库不存在、权限不足、GitHub API 异常只记录日志并继续
- Ollama 不可达、调用失败、或模型返回非法 JSON 时，自动回退到基础文本摘要
- 没有 Qdrant 也不会阻断主流程

## Ollama 角色模型说明

- 推荐先在仓库根目录执行 `.\ollama\build-models.ps1` 构建 5 个持久化角色模型
- domain 到模型映射在 `config/ollama_models.yaml`
- `OLLAMA_MODEL_OVERRIDE` 环境变量可临时强制覆盖所有 domain 模型（调试用途，推荐）
- `OLLAMA_MODEL` 仍保留历史兼容，但不建议长期使用
- `OLLAMA_SYSTEM_PROMPT` 可临时覆盖 system prompt（调试用途）

## 手动运行（容器）

```powershell
docker compose --env-file .\compose\.env -f .\compose\docker-compose.yml run --rm github-watch python -m app.main
```

## Ollama Base URL 自动判定

- 优先使用 `OLLAMA_BASE_URL`
- 若为空，回退 `OLLAMA_HOST`（兼容历史配置）
- 若都为空，自动判定运行环境：
  - 宿主机直跑默认优先 `http://127.0.0.1:11434`
  - 容器内运行默认优先 `http://host.docker.internal:11434`
- 启动时会做短超时可达性探测；若都不可达，仍返回环境对应的确定性兜底地址
