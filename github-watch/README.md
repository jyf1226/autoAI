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
6. 加载 `config/prompts/*.md` 生成 Ollama 提示词
7. 输出全局日报到 `reports/daily/`
8. 输出按 domain 日报到 `reports/by-domain/`
9. 预留 embeddings / training-samples exporter

## exporter 状态

- `markdown_exporter.py`: 实际使用
- `qdrant_exporter.py`: stub，占位，不写入远端
- `training_exporter.py`: stub，占位，先生成 placeholder

## 容错策略

- 单仓库失败不影响整批任务
- 仓库不存在、权限不足、GitHub API 异常只记录日志并继续
- Ollama 失败时自动回退到基础文本摘要
- 没有 Qdrant 也不会阻断主流程

## 手动运行（容器）

```powershell
docker compose --env-file .\compose\.env -f .\compose\docker-compose.yml run --rm github-watch python -m app.main
```
