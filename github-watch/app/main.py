import datetime as dt
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import yaml

from app.build_daily_report import build_daily_report_markdown
from app.fetch_github import GitHubClient
from app.normalize_events import normalize_repo_events
from app.summarize_with_ollama import summarize_with_ollama

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
LOGGER = logging.getLogger("github-watch")


def _load_repos(config_path: Path) -> list[dict[str, str]]:
    with config_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    repos = cfg.get("repos", [])
    if not repos:
        raise ValueError(f"repos is empty in {config_path}")
    return repos


def _ensure_dirs(data_dir: Path) -> dict[str, Path]:
    targets = {
        "raw": data_dir / "raw",
        "normalized": data_dir / "normalized",
        "reports": data_dir / "reports",
    }
    for p in targets.values():
        p.mkdir(parents=True, exist_ok=True)
    return targets


def _write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def run_once() -> None:
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required")

    repos_file = Path(os.getenv("GITHUB_WATCH_REPOS_FILE", "/app/config/repos.yaml"))
    data_dir = Path(os.getenv("GITHUB_WATCH_DATA_DIR", "/data"))
    api_base = os.getenv("GITHUB_API_BASE_URL", "https://api.github.com")
    ollama_base = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    sleep_s = float(os.getenv("GITHUB_WATCH_REQUEST_SLEEP_SECONDS", "1"))

    paths = _ensure_dirs(data_dir)
    repos = _load_repos(repos_file)
    client = GitHubClient(token=token, base_url=api_base, request_sleep_seconds=sleep_s)

    now_utc = dt.datetime.now(dt.timezone.utc)
    since_utc = now_utc - dt.timedelta(hours=24)
    stamp = now_utc.strftime("%Y%m%d-%H%M%S")

    normalized_batch: list[dict[str, Any]] = []
    for item in repos:
        owner = item["owner"]
        repo = item["repo"]
        repo_key = f"{owner}_{repo}"
        LOGGER.info("Processing %s/%s", owner, repo)
        raw = client.fetch_recent(owner=owner, repo=repo, since_utc=since_utc)
        raw_path = paths["raw"] / f"{stamp}-{repo_key}.json"
        _write_json(raw_path, raw)
        normalized = normalize_repo_events(owner=owner, repo=repo, raw_events=raw)
        normalized_batch.append(normalized)
        normalized_path = paths["normalized"] / f"{stamp}-{repo_key}.json"
        _write_json(normalized_path, normalized)

    summary = summarize_with_ollama(normalized_batch, ollama_base_url=ollama_base, model=ollama_model)
    report_markdown = build_daily_report_markdown(now_utc, normalized_batch, summary)
    report_path = paths["reports"] / f"{now_utc.strftime('%Y-%m-%d')}.md"
    report_path.write_text(report_markdown, encoding="utf-8")
    LOGGER.info("Report generated: %s", report_path)


def main() -> None:
    poll_interval = int(os.getenv("GITHUB_WATCH_POLL_INTERVAL_SECONDS", "3600"))
    while True:
        try:
            run_once()
        except Exception as exc:
            LOGGER.exception("Run failed: %s", exc)
        LOGGER.info("Sleep %s seconds before next run", poll_interval)
        time.sleep(max(30, poll_interval))


if __name__ == "__main__":
    main()
