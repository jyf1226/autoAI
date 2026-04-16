from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import requests
import yaml

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

DEFAULT_DOMAIN_MODEL_MAP = {
    "games": "gh-games-qw-14b",
    "image-processing": "gh-image-qw-14b",
    "short-video": "gh-video-qw-14b",
    "finance": "gh-finance-qw-14b",
    "infra": "gh-research-qw-14b",
    "default": "gh-research-qw-14b",
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


def _load_domain_model_map(config_file: Path) -> dict[str, str]:
    if not config_file.exists():
        return dict(DEFAULT_DOMAIN_MODEL_MAP)
    try:
        payload = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        LOGGER.warning("Failed to load %s: %s", config_file, exc)
        return dict(DEFAULT_DOMAIN_MODEL_MAP)
    mapping = payload.get("domain_models", {})
    if not isinstance(mapping, dict):
        return dict(DEFAULT_DOMAIN_MODEL_MAP)
    normalized = dict(DEFAULT_DOMAIN_MODEL_MAP)
    for key, value in mapping.items():
        domain = str(key).strip()
        model = str(value).strip()
        if domain and model:
            normalized[domain] = model
    return normalized


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


def _render_multi_domain_markdown(reports: list[tuple[str, str]]) -> str:
    lines: list[str] = ["# 今日 GitHub 研究日报"]
    for domain, markdown in reports:
        lines.append(f"\n## domain: {domain}")
        body = markdown.strip()
        if not body:
            lines.append("- 信息不足")
            continue
        for line in body.splitlines():
            if line.startswith("# "):
                continue
            if line.startswith("## "):
                lines.append(f"### {line[3:]}")
                continue
            lines.append(line)
    return "\n".join(lines).strip()


def _select_model_for_domain(domain: str, mapping: dict[str, str], default_model: str) -> str:
    override = os.getenv("OLLAMA_MODEL_OVERRIDE", "").strip()
    if override:
        LOGGER.info("Model routing: domain=%s source=env:OLLAMA_MODEL_OVERRIDE", domain)
        return override

    legacy_override = os.getenv("OLLAMA_MODEL", "").strip()
    if legacy_override:
        LOGGER.warning(
            "Model routing: domain=%s source=env:OLLAMA_MODEL (legacy global override). "
            "Prefer OLLAMA_MODEL_OVERRIDE for temporary debugging.",
            domain,
        )
        return legacy_override

    domain_model = mapping.get(domain, "").strip()
    if domain_model:
        LOGGER.info("Model routing: domain=%s source=domain-map", domain)
        return domain_model

    default_map_model = mapping.get("default", "").strip()
    if default_map_model:
        LOGGER.info("Model routing: domain=%s source=domain-map-default", domain)
        return default_map_model

    LOGGER.info("Model routing: domain=%s source=settings-default", domain)
    return default_model


def _build_prompt(
    domain: str,
    events: list[dict[str, Any]],
    prompts_dir: Path,
    system_prompt_override: str | None = None,
) -> str:
    daily_prompt = load_text(prompts_dir / "daily_report.md", default="请用中文生成日报摘要。")
    domain_prompt_file = DOMAIN_PROMPT_FILES.get(domain)
    domain_prompt = load_text(prompts_dir / domain_prompt_file, default="") if domain_prompt_file else ""
    system_prompt = (system_prompt_override or os.getenv("OLLAMA_SYSTEM_PROMPT", "")).strip()
    if not system_prompt:
        system_prompt = "你是一个用于 GitHub 仓库更新研究的中文分析助手。输出必须简洁、结构化、可执行。"
    return (
        f"{system_prompt}\n\n"
        "请基于输入数据输出严格 JSON，禁止输出 JSON 以外的内容。\n\n"
        "输出要求：\n"
        "1. 使用中文、每条一句话，避免长篇发散\n"
        "2. 重点覆盖：核心变化、值得研究、项目启发、风险备注\n"
        "3. 信息不足时明确写“信息不足”\n"
        "4. 不要输出思维过程\n\n"
        f"全局日报规则：\n{daily_prompt}\n\n"
        f"当前 domain={domain} 的补充规则：\n{domain_prompt}\n\n"
        f"输入数据(JSON):\n{json.dumps(events, ensure_ascii=False)}"
    )


def _call_ollama_json(
    ollama_base_url: str,
    model: str,
    prompt: str,
    timeout_seconds: int,
) -> dict[str, list[str]]:
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
    response = requests.post(
        f"{ollama_base_url.rstrip('/')}/api/generate",
        json=payload,
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    result = response.json()
    raw_text = str(result.get("response", "")).strip()
    if not raw_text:
        return _normalize_report_json({})
    report_json = json.loads(raw_text)
    if not isinstance(report_json, dict):
        raise ValueError("model response is not a JSON object")
    return _normalize_report_json(report_json)


def summarize_with_ollama(
    normalized_events: list[dict[str, Any]],
    ollama_base_url: str,
    model: str,
    prompts_dir: Path,
    timeout_seconds: int = 120,
    system_prompt_override: str | None = None,
    domain_model_map_file: Path | None = None,
) -> str:
    mapping_file = domain_model_map_file or (prompts_dir.parent / "ollama_models.yaml")
    domain_model_map = _load_domain_model_map(mapping_file)
    events_by_domain: dict[str, list[dict[str, Any]]] = {}
    for item in normalized_events:
        events_by_domain.setdefault(item.get("domain", "default"), []).append(item)

    reports: list[tuple[str, str]] = []
    for domain, events in sorted(events_by_domain.items()):
        selected_model = _select_model_for_domain(domain, domain_model_map, model)
        LOGGER.info("Summarizing domain=%s with model=%s", domain, selected_model)
        prompt = _build_prompt(
            domain=domain,
            events=events,
            prompts_dir=prompts_dir,
            system_prompt_override=system_prompt_override,
        )
        try:
            normalized_report = _call_ollama_json(
                ollama_base_url=ollama_base_url,
                model=selected_model,
                prompt=prompt,
                timeout_seconds=timeout_seconds,
            )
            reports.append((domain, _render_markdown_report(normalized_report)))
        except (ValueError, json.JSONDecodeError) as exc:
            LOGGER.exception("Failed to parse model JSON response for domain=%s model=%s: %s", domain, selected_model, exc)
            reports.append((domain, build_fallback_summary(events, f"【无模型摘要模式】domain={domain} 模型输出解析失败: {exc}")))
        except requests.RequestException as exc:
            LOGGER.exception("Failed to call Ollama API for domain=%s model=%s: %s", domain, selected_model, exc)
            reports.append((domain, build_fallback_summary(events, f"【无模型摘要模式】domain={domain} Ollama 调用失败: {exc}")))

    if not reports:
        return build_fallback_summary(normalized_events, "【无模型摘要模式】今日无显著变更。")
    return _render_multi_domain_markdown(reports)


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
