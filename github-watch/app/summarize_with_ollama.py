import json
import logging
from typing import Any

import requests

LOGGER = logging.getLogger(__name__)

OLLAMA_PROMPT_TEMPLATE = """
你是一个游戏项目技术研究助手。请基于输入的 GitHub 更新数据，用中文输出简洁日报摘要。

输出要求：
1) 先给出 3-5 行总体结论
2) 按 group 分组，每组给出：
   - 今日有更新的 repo
   - 核心变化摘要
   - 值得重点研究的改动
   - 对个人项目的可迁移启发
3) 不要编造数据；没有更新请明确写“无显著更新”
4) 风格务实、工程化、可执行
""".strip()


def summarize_with_ollama(
    normalized_events: list[dict[str, Any]],
    ollama_base_url: str,
    model: str,
    timeout_seconds: int = 120,
) -> str:
    prompt = f"{OLLAMA_PROMPT_TEMPLATE}\n\n输入数据(JSON):\n{json.dumps(normalized_events, ensure_ascii=False)}"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    try:
        response = requests.post(
            f"{ollama_base_url.rstrip('/')}/api/generate",
            json=payload,
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip() or "【无模型摘要模式】今日无显著变更。"
    except requests.RequestException as exc:
        LOGGER.exception("Failed to call Ollama API: %s", exc)
        return _fallback_summary(normalized_events, f"【无模型摘要模式】Ollama 调用失败: {exc}")


def _fallback_summary(normalized_events: list[dict[str, Any]], title: str) -> str:
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in normalized_events:
        groups.setdefault(item.get("group", "未分组"), []).append(item)
    lines = [title]
    for group_name, repos in groups.items():
        lines.append(f"- {group_name}")
        for repo in repos:
            lines.append(
                f"  - {repo.get('repo')}: commits={len(repo.get('commits', []))}, "
                f"PR={len(repo.get('pull_requests', []))}, issues={len(repo.get('issues', []))}"
            )
    return "\n".join(lines)
