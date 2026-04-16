# 最小验收清单（MVP）

适用场景：执行 `.\start.ps1` 或单独运行 `github-watch` 后，快速确认链路是否可用。

## 1) 目录检查（必须存在）

- `data/github-watch/raw/`
- `data/github-watch/normalized/`
- `data/github-watch/reports/daily/`
- `data/github-watch/reports/by-domain/`
- `data/github-watch/state/`

## 2) 日报文件检查（至少 1 份）

- `data/github-watch/reports/daily/` 下有当日 Markdown 文件
- `data/github-watch/reports/by-domain/` 下每个已配置 domain 至少有 1 份 Markdown 文件
- 如果 Ollama 不可用，日报允许出现“无模型摘要模式”字样（属于预期兜底）

## 3) 规范化数据检查（至少 1 份）

- `data/github-watch/normalized/<domain>/` 下有新的 JSON 文件
- JSON 中每条 commit / PR / issue 事件包含以下预留字段：
  - `doc_id`
  - `metadata`
  - `chunk_source`

> 说明：这些字段用于未来 Qdrant 接入，目前只做结构预留，不生成真实 embedding。

## 4) 服务地址检查

- Open WebUI: `http://localhost:3000`
- Qdrant: `http://localhost:6333`
- n8n: `http://localhost:5678`
- Ollama API（宿主机常见地址）: `http://127.0.0.1:11434`

## 5) exporter 状态确认（当前版本）

- 生效：`github-watch/app/exporters/markdown_exporter.py`
- stub：`github-watch/app/exporters/qdrant_exporter.py`
- stub：`github-watch/app/exporters/training_exporter.py`
