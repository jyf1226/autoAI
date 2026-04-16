import json
import logging
from typing import Any

import requests

LOGGER = logging.getLogger(__name__)


def summarize_with_ollama(
    normalized_events: list[dict[str, Any]],
    ollama_base_url: str,
    model: str,
) -> str:
    prompt = {
        "task": "请用中文生成 GitHub 每日报告摘要。",
        "要求": [
            "按仓库分组",
            "先给总体结论，再给重点变化",
            "指出风险和建议跟进项",
            "保持简洁，适合贴到日报",
        ],
        "data": normalized_events,
    }

    payload = {
        "model": model,
        "prompt": json.dumps(prompt, ensure_ascii=False),
        "stream": False,
    }

    try:
        response = requests.post(
            f"{ollama_base_url.rstrip('/')}/api/generate",
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip() or "今日无显著变更。"
    except requests.RequestException as exc:
        LOGGER.exception("Failed to call Ollama API: %s", exc)
        return "Ollama 总结生成失败，请检查宿主机 Ollama 服务。"
import json
import logging
from typing import Any

import requests

LOGGER = logging.getLogger(__name__)


def summarize_with_ollama(
    normalized_events: list[dict[str, Any]],
    ollama_base_url: str,
    model: str,
) -> str:
    prompt = {
        "task": "请用中文生成 GitHub 每日报告摘要。",
        "要求": [
            "按仓库分组",
            "先给总体结论，再给重点变化",
            "指出风险和建议跟进项",
            "保持简洁，适合贴到日报",
        ],
        "data": normalized_events,
    }

    payload = {
        "model": model,
        "prompt": json.dumps(prompt, ensure_ascii=False),
        "stream": False,
    }

    try:
        response = requests.post(
            f"{ollama_base_url.rstrip('/')}/api/generate",
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip() or "今日无显著变更。"
    except requests.RequestException as exc:
        LOGGER.exception("Failed to call Ollama API: %s", exc)
        return "Ollama 总结生成失败，请检查宿主机 Ollama 服务。"
