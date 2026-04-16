# github-watch

一个最小可运行的 GitHub 动态日报服务。

## 功能

1. 读取 `config/repos.yaml`
2. 拉取最近 24 小时 commits / pull requests / issues
3. 保存原始 JSON 到 `data/github-watch/raw/`
4. 保存规范化 JSON 到 `data/github-watch/normalized/`
5. 调用宿主机 Ollama 生成中文摘要
6. 输出 Markdown 报告到 `data/github-watch/reports/`

## 环境变量

从 `compose/.env` 注入：

- `GITHUB_TOKEN`
- `GITHUB_API_BASE_URL`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `GITHUB_WATCH_REPOS_FILE`
- `GITHUB_WATCH_DATA_DIR`
- `GITHUB_WATCH_POLL_INTERVAL_SECONDS`
- `GITHUB_WATCH_REQUEST_SLEEP_SECONDS`

## 本地调试（可选）

在项目根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r .\github-watch\requirements.txt
$env:GITHUB_TOKEN="你的token"
$env:GITHUB_WATCH_REPOS_FILE="E:\aiauto\github-watch\config\repos.yaml"
$env:GITHUB_WATCH_DATA_DIR="E:\aiauto\data\github-watch"
python -m github-watch.app.main
```
