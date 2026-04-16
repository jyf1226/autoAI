import datetime as dt
from typing import Any


def build_daily_report_markdown(
    generated_at: dt.datetime,
    normalized_events: list[dict[str, Any]],
    summary_text: str,
) -> str:
    lines: list[str] = []
    lines.append(f"# GitHub 每日报告 - {generated_at.strftime('%Y-%m-%d')}")
    lines.append("")
    lines.append(f"生成时间: {generated_at.isoformat()}")
    lines.append("")
    lines.append("## AI 摘要")
    lines.append("")
    lines.append(summary_text)
    lines.append("")
    lines.append("## 数据概览")
    lines.append("")
    for repo_item in normalized_events:
        stats = repo_item.get("stats", {})
        lines.append(
            f"- {repo_item.get('repo')}: commits={stats.get('commits', 0)}, "
            f"pulls={stats.get('pulls', 0)}, issues={stats.get('issues', 0)}"
        )
    lines.append("")
    lines.append("## 详细变更")
    lines.append("")
    for repo_item in normalized_events:
        lines.append(f"### {repo_item.get('repo')}")
        lines.append("")
        _append_section(lines, "Commits", repo_item.get("commits", []), key_map={"title": "message", "time": "date"})
        _append_section(lines, "Pull Requests", repo_item.get("pulls", []), key_map={"id": "number", "title": "title", "time": "updated_at"})
        _append_section(lines, "Issues", repo_item.get("issues", []), key_map={"id": "number", "title": "title", "time": "updated_at"})
    lines.append("")
    return "\n".join(lines)


def _append_section(lines: list[str], title: str, items: list[dict[str, Any]], key_map: dict[str, str]) -> None:
    lines.append(f"#### {title}")
    if not items:
        lines.append("")
        lines.append("- 无")
        lines.append("")
        return
    lines.append("")
    for item in items:
        item_id = item.get(key_map.get("id", ""), "")
        item_title = item.get(key_map["title"], "")
        item_time = item.get(key_map["time"], "")
        item_url = item.get("url", "")
        prefix = f"#{item_id} " if item_id else ""
        lines.append(f"- {prefix}{item_title} ({item_time}) {item_url}".strip())
    lines.append("")
