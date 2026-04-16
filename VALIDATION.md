# 验收记录（MVP v1 基线）

- 验收日期：2026-04-16
- 验收环境：Windows 11 + PowerShell + Docker Desktop（WSL2）+ 本地 Ollama（含不可用回退场景）
- 四项通过：`raw/normalized` 持续产物、`daily/by-domain` 按日期生成、`state` 二次运行去重、Ollama 停止后基础中文日报回退
- state 去重修正：`last_fetched + 1s`
- Ollama 502 回退：已验证（日报可生成，进入“无模型摘要模式”）
