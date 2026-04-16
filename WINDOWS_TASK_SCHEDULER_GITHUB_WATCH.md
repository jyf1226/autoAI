# Windows 任务计划程序示例（每日自动运行 github-watch）

下面给一个最小可用方案：每天固定时间执行一次 `github-watch` 容器任务。

## 方式 A：命令行一键创建任务（推荐）

先确保项目路径与 Docker 命令可用，然后在 PowerShell（管理员）执行：

```powershell
schtasks /Create /TN "AIAuto\github-watch-daily" /SC DAILY /ST 08:30 /F /TR "powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ""docker compose --env-file E:\aiauto\compose\.env -f E:\aiauto\compose\docker-compose.yml run --rm github-watch python -m app.main"""
```

## 方式 B：图形界面创建（关键参数）

1. 打开“任务计划程序” -> “创建任务”
2. 常规：
   - 名称：`github-watch-daily`
   - 勾选“使用最高权限运行”
3. 触发器：
   - 每天，时间例如 `08:30`
4. 操作：
   - 程序/脚本：`powershell.exe`
   - 添加参数：
     ```text
     -NoProfile -ExecutionPolicy Bypass -Command "docker compose --env-file E:\aiauto\compose\.env -f E:\aiauto\compose\docker-compose.yml run --rm github-watch python -m app.main"
     ```
   - 起始于：`E:\aiauto`

## 常见排错

- 若任务显示成功但无新日报：
  - 检查 `data/github-watch/reports/daily/` 是否有当天新文件
  - 检查 `compose/.env` 中 `GITHUB_TOKEN` 是否有效
  - 检查 Docker Desktop 与 Ollama 是否已启动
- 若任务历史报命令找不到：
  - 将 Docker Desktop 安装路径加入系统 `PATH`
  - 或在命令里改成 Docker 的绝对路径调用
