from typing import Any


def normalize_repo_events(owner: str, repo: str, raw_events: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    full_name = f"{owner}/{repo}"

    commits = [
        {
            "sha": item.get("sha"),
            "author": (item.get("commit") or {}).get("author", {}).get("name"),
            "message": (item.get("commit") or {}).get("message"),
            "date": (item.get("commit") or {}).get("author", {}).get("date"),
            "url": item.get("html_url"),
        }
        for item in raw_events.get("commits", [])
    ]
    pulls = [
        {
            "number": item.get("number"),
            "title": item.get("title"),
            "state": item.get("state"),
            "author": (item.get("user") or {}).get("login"),
            "updated_at": item.get("updated_at"),
            "url": item.get("html_url"),
        }
        for item in raw_events.get("pulls", [])
    ]
    issues = [
        {
            "number": item.get("number"),
            "title": item.get("title"),
            "state": item.get("state"),
            "author": (item.get("user") or {}).get("login"),
            "updated_at": item.get("updated_at"),
            "url": item.get("html_url"),
        }
        for item in raw_events.get("issues", [])
    ]

    return {
        "repo": full_name,
        "stats": {
            "commits": len(commits),
            "pulls": len(pulls),
            "issues": len(issues),
        },
        "commits": commits,
        "pulls": pulls,
        "issues": issues,
    }
