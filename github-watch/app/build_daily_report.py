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
    lines.append("## 分组快照")
    lines.append("")

    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in normalized_events:
        grouped.setdefault(item.get("group", "未分组"), []).append(item)

    for group_name, repos in grouped.items():
        lines.append(f"## {group_name}")
        lines.append("")
        lines.append("1. 今日有哪些 repo 有更新")
        active_repos = [x["repo"] for x in repos if _has_updates(x)]
        if active_repos:
            for repo_name in active_repos:
                lines.append(f"- {repo_name}")
        else:
            lines.append("- 无显著更新")
        lines.append("")

        lines.append("2. 核心变化摘要")
        for repo_item in repos:
            commit_count = len(repo_item.get("commits", []))
            pr_count = len(repo_item.get("pull_requests", []))
            issue_count = len(repo_item.get("issues", []))
            lines.append(f"- {repo_item.get('repo')}: commits={commit_count}, PR={pr_count}, issues={issue_count}")
        lines.append("")

        lines.append("3. 哪些改动值得我重点研究")
        highlights = _highlights(repos)
        if highlights:
            for point in highlights:
                lines.append(f"- {point}")
        else:
            lines.append("- 今日无明显高优先级改动")
        lines.append("")

        lines.append("4. 对我自己项目可能有什么启发")
        lines.append("- 关注多人联机同步与服务端状态一致性实现细节")
        lines.append("- 关注 PR/Issue 中的性能与可维护性讨论，作为技术选型参考")
        lines.append("")

    lines.append("")
    return "\n".join(lines)


def _has_updates(repo_item: dict[str, Any]) -> bool:
    return bool(repo_item.get("commits") or repo_item.get("pull_requests") or repo_item.get("issues"))


def _highlights(repos: list[dict[str, Any]]) -> list[str]:
    result: list[str] = []
    for repo_item in repos:
        repo = repo_item.get("repo")
        prs = repo_item.get("pull_requests", [])
        issues = repo_item.get("issues", [])
        commits = repo_item.get("commits", [])
        if prs:
            top = prs[0]
            result.append(f"{repo} PR #{top.get('number')} - {top.get('title')}")
        elif issues:
            top = issues[0]
            result.append(f"{repo} Issue #{top.get('number')} - {top.get('title')}")
        elif commits:
            top = commits[0]
            result.append(f"{repo} Commit - {top.get('title')}")
    return result[:8]
