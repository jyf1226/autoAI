from __future__ import annotations

from typing import Any

from app.models import NormalizedRepoData, TimeRange


def _labels(item: dict[str, Any]) -> list[str]:
    return [x.get("name", "") for x in item.get("labels", []) if isinstance(x, dict)]


def _qdrant_stub_fields(
    repo: str,
    domain: str,
    event_type: str,
    identity: Any,
    url: str,
) -> dict[str, Any]:
    identity_text = str(identity or "unknown")
    # Reserved payload shape for future Qdrant embedding pipeline.
    return {
        "doc_id": f"{repo}:{event_type}:{identity_text}",
        "metadata": {
            "repo": repo,
            "domain": domain,
            "event_type": event_type,
            "source_url": url,
        },
        "chunk_source": "full_text_v1",
    }


def normalize_repo_events(raw_events: dict[str, Any], fetched_at: str) -> dict[str, Any]:
    repo = raw_events.get("repo", "")
    domain = raw_events.get("domain", "unknown")
    normalized = NormalizedRepoData(
        repo=repo,
        domain=domain,
        group=raw_events.get("group", "未分组"),
        fetched_at=fetched_at,
        time_range=TimeRange(
            start=raw_events.get("since", ""),
            end=raw_events.get("until", ""),
        ),
    )

    for item in raw_events.get("commits", []):
        commit_data = item.get("commit", {})
        url = item.get("html_url", "")
        reserved = _qdrant_stub_fields(
            repo=repo,
            domain=domain,
            event_type="commit",
            identity=item.get("sha", ""),
            url=url,
        )
        normalized.commits.append(
            {
                "id": item.get("sha", ""),
                "number": None,
                "title": commit_data.get("message", "").split("\n")[0],
                "message": commit_data.get("message", ""),
                "author": (commit_data.get("author") or {}).get("name") or (item.get("author") or {}).get("login"),
                "created_at": (commit_data.get("author") or {}).get("date"),
                "updated_at": (commit_data.get("author") or {}).get("date"),
                "url": url,
                "labels": [],
                "changed_files": [],
                "summary_text": commit_data.get("message", ""),
                **reserved,
            }
        )

    for item in raw_events.get("pull_requests", []):
        title = item.get("title", "")
        body = item.get("body") or ""
        url = item.get("html_url", "")
        reserved = _qdrant_stub_fields(
            repo=repo,
            domain=domain,
            event_type="pull_request",
            identity=item.get("id"),
            url=url,
        )
        normalized.pull_requests.append(
            {
                "id": item.get("id"),
                "number": item.get("number"),
                "title": title,
                "message": body,
                "author": (item.get("user") or {}).get("login"),
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at"),
                "url": url,
                "labels": _labels(item),
                "changed_files": item.get("changed_files", []),
                "summary_text": f"{title}\n{body}".strip(),
                **reserved,
            }
        )

    for item in raw_events.get("issues", []):
        title = item.get("title", "")
        body = item.get("body") or ""
        url = item.get("html_url", "")
        reserved = _qdrant_stub_fields(
            repo=repo,
            domain=domain,
            event_type="issue",
            identity=item.get("id"),
            url=url,
        )
        normalized.issues.append(
            {
                "id": item.get("id"),
                "number": item.get("number"),
                "title": title,
                "message": body,
                "author": (item.get("user") or {}).get("login"),
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at"),
                "url": url,
                "labels": _labels(item),
                "changed_files": [],
                "summary_text": f"{title}\n{body}".strip(),
                **reserved,
            }
        )

    result = normalized.as_dict()
    result["error"] = raw_events.get("error")
    return result
