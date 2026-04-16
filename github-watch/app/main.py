from __future__ import annotations

import datetime as dt
import logging
import time

from app.build_daily_report import build_daily_report_markdown, build_domain_report_markdown
from app.config import load_settings
from app.exporters.markdown_exporter import export_domain_markdown, export_markdown
from app.exporters.qdrant_exporter import export_to_qdrant
from app.exporters.training_exporter import export_training_samples
from app.fetch_github import GitHubClient
from app.normalize_events import normalize_repo_events
from app.summarize_with_ollama import build_fallback_summary, summarize_with_ollama
from app.utils import ensure_runtime_dirs, from_iso, load_domain_configs, load_json, to_iso, utc_now, write_json

LOGGER = logging.getLogger("github-watch")


def _load_state(state_file):
    return load_json(state_file, {})


def _state_key(domain: str, repo_name: str) -> str:
    return f"{domain}:{repo_name}"


def _resolve_since(state: dict[str, str], key: str, default_since_text: str) -> str:
    return state.get(key, default_since_text)


def healthcheck() -> None:
    print("ok")


def run_once() -> None:
    settings = load_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    if not settings.github_token:
        LOGGER.warning("GITHUB_TOKEN is empty, fallback to unauthenticated GitHub API mode")

    dirs = ensure_runtime_dirs(settings.data_dir)
    state_file = dirs["state"] / "fetch_state.json"
    state = _load_state(state_file)
    domain_configs = load_domain_configs(settings.repos_dir)
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
    domain_buckets: dict[str, list[dict]] = {}

    for domain_cfg in domain_configs:
        domain_buckets.setdefault(domain_cfg.domain, [])
        for target in domain_cfg.targets:
            state_key = _state_key(target.domain, target.full_name)
            since_text = _resolve_since(state, state_key, default_since_text)
            try:
                since_utc = from_iso(since_text)
                raw_data = client.fetch_recent(target=target, since_utc=since_utc, until_utc=now)
                raw_data["error"] = None
            except Exception as exc:
                LOGGER.exception("fetch failed for %s", target.full_name)
                raw_data = {
                    "repo": target.full_name,
                    "domain": target.domain,
                    "group": target.group,
                    "since": since_text,
                    "until": now_text,
                    "commits": [],
                    "pull_requests": [],
                    "issues": [],
                    "error": str(exc),
                }

            write_json(dirs["domains"]["raw"][target.domain] / f"{stamp}-{target.key}.json", raw_data)
            normalized = normalize_repo_events(raw_data, fetched_at=now_text)
            normalized_batch.append(normalized)
            domain_buckets[target.domain].append(normalized)
            write_json(dirs["domains"]["normalized"][target.domain] / f"{stamp}-{target.key}.json", normalized)
            state[state_key] = now_text

    summary = summarize_with_ollama(
        normalized_events=normalized_batch,
        ollama_base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        prompts_dir=settings.prompts_dir,
        timeout_seconds=settings.ollama_timeout_seconds,
    )
    global_report = build_daily_report_markdown(now, normalized_batch, summary)
    global_path = export_markdown(
        dirs["reports"]["daily"],
        now,
        f"{now.strftime('%Y-%m-%d')}.md",
        global_report,
    )
    for domain, items in domain_buckets.items():
        domain_summary = build_fallback_summary(items, f"{domain} 基础摘要")
        domain_report = build_domain_report_markdown(now, domain, items, domain_summary)
        export_domain_markdown(dirs["reports"]["by-domain"], domain, now, domain_report)

    weekly_placeholder = dirs["reports"]["weekly"] / f"{now.strftime('%Y-%W')}.md"
    if not weekly_placeholder.exists():
        weekly_placeholder.write_text("# Weekly report placeholder\n", encoding="utf-8")

    export_to_qdrant(normalized_batch, dirs["embeddings"])
    export_training_samples(normalized_batch, dirs["training-samples"])
    write_json(state_file, state)
    LOGGER.info("global report generated: %s", global_path)


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
