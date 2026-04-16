# github-watch

`github-watch` 是本项目的核心自动研究服务，负责抓取 GitHub 更新并生成中文日报。

## 处理流程

1. 读取 `config/repos.yaml` 分组仓库配置
2. 按仓库读取 `data/github-watch/state/fetch_state.json` 计算抓取窗口
3. 拉取 commits / pull requests / issues
4. 保存原始 JSON 到 `data/github-watch/raw/`
5. 规范化为统一结构写入 `data/github-watch/normalized/`
6. 调用宿主机 Ollama 生成中文摘要（失败自动降级）
7. 输出 Markdown 到 `data/github-watch/reports/`
8. 更新 state，避免重复抓取

## 容错策略

- 单仓库失败不影响整体流程
- GitHub API 基础重试与速率限制等待
- Ollama 调用失败自动切换到无模型摘要模式

## 手动运行（容器）

```powershell
docker compose --env-file .\compose\.env -f .\compose\docker-compose.yml run --rm github-watch python -m app.main
```

## 后续扩展位

- 在 `normalize_events.py` 后增加 `to_qdrant_documents(...)`
- 在 `main.py` 正常化后插入“写入向量库 / 训练样本导出”步骤
