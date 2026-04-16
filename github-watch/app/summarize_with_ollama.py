from __future__ import annotations

import json
import logging
import os
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

REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "core_changes": {"type": "array", "items": {"type": "string"}},
        "worth_studying": {"type": "array", "items": {"type": "string"}},
        "project_insights": {"type": "array", "items": {"type": "string"}},
        "risk_notes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["core_changes", "worth_studying", "project_insights", "risk_notes"],
    "additionalProperties": False,
}


def _to_float(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        LOGGER.warning("Invalid %s=%r, fallback to %s", name, raw, default)
        return default


def _to_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        LOGGER.warning("Invalid %s=%r, fallback to %s", name, raw, default)
        return default


def _normalize_report_json(report: dict[str, Any]) -> dict[str, list[str]]:
    normalized: dict[str, list[str]] = {}
    for key in ("core_changes", "worth_studying", "project_insights", "risk_notes"):
        values = report.get(key, [])
        if not isinstance(values, list):
            values = [str(values)] if values else []
        normalized[key] = [str(item).strip() for item in values if str(item).strip()]
    return normalized


def _render_markdown_report(report: dict[str, list[str]]) -> str:
    sections = [
        ("核心变化", report["core_changes"]),
        ("值得研究", report["worth_studying"]),
        ("项目启发", report["project_insights"]),
        ("风险备注", report["risk_notes"]),
    ]
    lines: list[str] = ["# 今日 GitHub 研究日报"]
    for title, items in sections:
        lines.append(f"\n## {title}")
        if not items:
            lines.append("- 信息不足")
            continue
        lines.extend(f"- {item}" for item in items)
    return "\n".join(lines).strip()


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
        "你是一个用于 GitHub 仓库更新研究的中文分析助手。"
        "请基于输入数据输出严格 JSON，禁止输出 JSON 以外的内容。\n\n"
        "输出要求：\n"
        "1. 使用中文\n"
        "2. 不要复述大量原文\n"
        "3. 重点关注：核心变化、值得研究点、对项目启发、风险备注\n"
        "4. 信息不足时写“信息不足”\n\n"
        f"{daily_prompt}\n\n"
        f"各 domain 总结提示：\n{chr(10).join(repo_prompt_lines)}\n\n"
        f"输入数据(JSON):\n{json.dumps(normalized_events, ensure_ascii=False)}"
    )
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "keep_alive": os.getenv("OLLAMA_KEEP_ALIVE", "30m").strip() or "30m",
        "format": REPORT_SCHEMA,
        "options": {
            "num_ctx": _to_int("OLLAMA_NUM_CTX", 8192),
            "temperature": _to_float("OLLAMA_TEMPERATURE", 0.2),
            "top_p": _to_float("OLLAMA_TOP_P", 0.9),
            "repeat_penalty": _to_float("OLLAMA_REPEAT_PENALTY", 1.05),
        },
    }

    try:
        response = requests.post(
            f"{ollama_base_url.rstrip('/')}/api/generate",
            json=payload,
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        result = response.json()
        raw_text = result.get("response", "").strip()
        if not raw_text:
            return "【无模型摘要模式】今日无显著变更。"
        report_json = json.loads(raw_text)
        if not isinstance(report_json, dict):
            raise ValueError("model response is not a JSON object")
        normalized_report = _normalize_report_json(report_json)
        return _render_markdown_report(normalized_report)
    except (ValueError, json.JSONDecodeError) as exc:
        LOGGER.exception("Failed to parse model JSON response: %s", exc)
        return build_fallback_summary(normalized_events, f"【无模型摘要模式】模型输出解析失败: {exc}")
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
