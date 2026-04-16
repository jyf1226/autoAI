from __future__ import annotations

import datetime as dt
import logging
import time
from pathlib import Path

import yaml

from app.build_daily_report import build_daily_report_markdown
from app.config import load_settings
from app.fetch_github import GitHubClient
from app.models import RepoTarget
from app.normalize_events import normalize_repo_events
from app.summarize_with_ollama import summarize_with_ollama
from app.utils import ensure_runtime_dirs, from_iso, load_json, to_iso, utc_now, write_json

LOGGER = logging.getLogger("github-watch")


def _load_targets(repos_file: Path) -> list[RepoTarget]:
    data = yaml.safe_load(repos_file.read_text(encoding="utf-8")) or {}
    groups = data.get("groups", {})
    targets: list[RepoTarget] = []
    for group_name, repos in groups.items():
        for full in repos or []:
            if "/" not in full:
                LOGGER.warning("skip invalid repo format: %s", full)
                continue
            owner, repo = full.split("/", 1)
            targets.append(RepoTarget(group=group_name, owner=owner, repo=repo))
    return targets


def _load_state(state_file: Path) -> dict[str, str]:
    return load_json(state_file, {})


def _resolve_since(state: dict[str, str], repo_name: str, default_since_text: str) -> str:
    return state.get(repo_name, default_since_text)


def healthcheck() -> None:
    print("ok")


def run_once() -> None:
    settings = load_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    if not settings.github_token:
        raise RuntimeError("GITHUB_TOKEN is required")

    dirs = ensure_runtime_dirs(settings.data_dir)
    state_file = dirs["state"] / "fetch_state.json"
    state = _load_state(state_file)
    targets = _load_targets(settings.repos_file)
    client = GitHubClient(
        token=settings.github_token,
        base_url=settings.github_api_base_url,
        request_sleep_seconds=settings.request_sleep_seconds,
        timeout_seconds=settings.http_timeout_seconds,
        max_retries=settings.max_retries,
    )

    now = utc_now()
    now_text = to_iso(now)
    default_since_text = to_iso(now - dt.timedelta(hours=24))
    stamp = now.strftime("%Y%m%d-%H%M%S")
    normalized_batch: list[dict] = []

    for target in targets:
        since_text = _resolve_since(state, target.full_name, default_since_text)
        try:
            since_utc = from_iso(since_text)
            raw_data = client.fetch_recent(target=target, since_utc=since_utc, until_utc=now)
            raw_data["error"] = None
        except Exception as exc:
            LOGGER.exception("fetch failed for %s", target.full_name)
            raw_data = {
                "repo": target.full_name,
                "group": target.group,
                "since": since_text,
                "until": now_text,
                "commits": [],
                "pull_requests": [],
                "issues": [],
                "error": str(exc),
            }

        write_json(dirs["raw"] / f"{stamp}-{target.key}.json", raw_data)
        normalized = normalize_repo_events(raw_data, fetched_at=now_text)
        normalized_batch.append(normalized)
        write_json(dirs["normalized"] / f"{stamp}-{target.key}.json", normalized)
        state[target.full_name] = now_text

    summary = summarize_with_ollama(
        normalized_events=normalized_batch,
        ollama_base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout_seconds=settings.ollama_timeout_seconds,
    )
    report = build_daily_report_markdown(now, normalized_batch, summary)
    report_path = dirs["reports"] / f"{now.strftime('%Y-%m-%d')}.md"
    report_path.write_text(report, encoding="utf-8")
    write_json(state_file, state)
    LOGGER.info("report generated: %s", report_path)


def main() -> None:
    settings = load_settings()
    while True:
        try:
            run_once()
        except Exception as exc:
            LOGGER.exception("run failed: %s", exc)
        LOGGER.info("sleep %s seconds", settings.poll_interval_seconds)
        time.sleep(max(30, settings.poll_interval_seconds))


if __name__ == "__main__":
    main()
