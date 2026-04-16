from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests

from app.domain_rules import get_domain_rule
from app.utils import load_text

LOGGER = logging.getLogger(__name__)

DOMAIN_PROMPT_FILES = {
    "games": "repo_summary_game.md",
    "image-processing": "repo_summary_image.md",
    "short-video": "repo_summary_video.md",
    "finance": "repo_summary_finance.md",
    "infra": "repo_summary_infra.md",
}


def summarize_with_ollama(
    normalized_events: list[dict[str, Any]],
    ollama_base_url: str,
    model: str,
    prompts_dir: Path,
    timeout_seconds: int = 120,
) -> str:
    daily_prompt = load_text(prompts_dir / "daily_report.md", default="请用中文生成日报摘要。")
    repo_prompt_lines: list[str] = []
    for domain, filename in DOMAIN_PROMPT_FILES.items():
        repo_prompt_lines.append(f"[{domain}]")
        repo_prompt_lines.append(load_text(prompts_dir / filename, default=""))
    prompt = (
        f"{daily_prompt}\n\n"
        f"各 domain 总结提示：\n{chr(10).join(repo_prompt_lines)}\n\n"
        f"输入数据(JSON):\n{json.dumps(normalized_events, ensure_ascii=False)}"
    )
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
        return build_fallback_summary(normalized_events, f"【无模型摘要模式】Ollama 调用失败: {exc}")


def build_fallback_summary(normalized_events: list[dict[str, Any]], title: str) -> str:
    domains: dict[str, list[dict[str, Any]]] = {}
    for item in normalized_events:
        domains.setdefault(item.get("domain", "unknown"), []).append(item)
    lines = [title]
    for domain_name, repos in domains.items():
        rule = get_domain_rule(domain_name)
        lines.append(f"- domain={domain_name}")
        lines.append(f"  - 关注角度: {rule.get('research_angle', '')}")
        for repo in repos:
            lines.append(
                f"  - {repo.get('repo')}: commits={len(repo.get('commits', []))}, "
                f"PR={len(repo.get('pull_requests', []))}, issues={len(repo.get('issues', []))}"
            )
    return "\n".join(lines)
