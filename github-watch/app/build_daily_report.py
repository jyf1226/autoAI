from __future__ import annotations

import datetime as dt
from typing import Any

from app.domain_rules import get_domain_rule


def build_daily_report_markdown(
    generated_at: dt.datetime,
    normalized_events: list[dict[str, Any]],
    summary_text: str,
    title: str = "GitHub 全局每日报告",
) -> str:
    lines: list[str] = []
    lines.append(f"# {title} - {generated_at.strftime('%Y-%m-%d')}")
    lines.append("")
    lines.append(f"生成时间: {generated_at.isoformat()}")
    lines.append("")
    lines.append("## AI 摘要")
    lines.append("")
    lines.append(summary_text)
    lines.append("")
    lines.append("## Domain 汇总")
    lines.append("")

    domains = _group_by(normalized_events, "domain")
    for domain_name, domain_items in domains.items():
        lines.append(f"## Domain: {domain_name}")
        lines.append("")
        lines.extend(_group_sections(domain_items, domain_name))
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def build_domain_report_markdown(
    generated_at: dt.datetime,
    domain: str,
    normalized_events: list[dict[str, Any]],
    summary_text: str,
) -> str:
    return build_daily_report_markdown(
        generated_at=generated_at,
        normalized_events=normalized_events,
        summary_text=summary_text,
        title=f"{domain} 每日报告",
    )


def _group_sections(domain_items: list[dict[str, Any]], domain_name: str) -> list[str]:
    lines: list[str] = []
    grouped = _group_by(domain_items, "group")
    domain_rule = get_domain_rule(domain_name)
    for group_name, repos in grouped.items():
        lines.append(f"### {group_name}")
        lines.append("")
        lines.append("1. 今日有哪些 repo 有更新")
        active_repos = [item["repo"] for item in repos if _has_updates(item)]
        if active_repos:
            lines.extend([f"- {repo_name}" for repo_name in active_repos])
        else:
            lines.append("- 无显著更新")
        lines.append("")

        lines.append("2. 核心变化摘要")
        for repo_item in repos:
            lines.append(
                f"- {repo_item.get('repo')}: commits={len(repo_item.get('commits', []))}, "
                f"PR={len(repo_item.get('pull_requests', []))}, issues={len(repo_item.get('issues', []))}"
            )
        lines.append("")

        lines.append("3. 哪些改动值得我重点研究")
        highlights = _highlights(repos, domain_rule.get("keywords", []))
        if highlights:
            lines.extend([f"- {item}" for item in highlights])
        else:
            lines.append(f"- 今日无明显高优先级改动，可按 {domain_rule.get('research_angle', '通用研究角度')} 继续观察")
        lines.append("")

        lines.append("4. 对我自己项目可能有什么启发")
        lines.append(f"- {domain_rule.get('inspiration_angle', '关注通用工程抽象与可迁移模式。')}")
        lines.append(f"- {domain_rule.get('research_angle', '优先关注可落地、可复用、可维护的实现方式。')}")
        lines.append("")
    return lines


def _group_by(items: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        grouped.setdefault(item.get(key, "unknown"), []).append(item)
    return grouped


def _has_updates(repo_item: dict[str, Any]) -> bool:
    return bool(repo_item.get("commits") or repo_item.get("pull_requests") or repo_item.get("issues"))


def _highlights(repos: list[dict[str, Any]], keywords: list[str]) -> list[str]:
    results: list[str] = []
    lowered_keywords = [item.lower() for item in keywords]
    for repo_item in repos:
        repo = repo_item.get("repo", "")
        for bucket_name in ["pull_requests", "issues", "commits"]:
            for item in repo_item.get(bucket_name, []):
                text = f"{item.get('title', '')}\n{item.get('message', '')}\n{item.get('summary_text', '')}".lower()
                if not lowered_keywords or any(keyword in text for keyword in lowered_keywords):
                    label = bucket_name[:-1] if bucket_name.endswith("s") else bucket_name
                    number = item.get("number")
                    prefix = f"{label.upper()} #{number}" if number else label.upper()
                    results.append(f"{repo} {prefix} - {item.get('title') or item.get('message')}")
                    break
            if results and results[-1].startswith(repo):
                break
    return results[:8]
