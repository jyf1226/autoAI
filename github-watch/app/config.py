from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    github_token: str
    github_api_base_url: str
    repos_dir: Path
    prompts_dir: Path
    pipelines_file: Path
    data_dir: Path
    poll_interval_seconds: int
    request_sleep_seconds: float
    http_timeout_seconds: int
    max_retries: int
    log_level: str
    ollama_base_url: str
    ollama_model: str
    ollama_timeout_seconds: int


def load_settings() -> Settings:
    config_root = Path(os.getenv("GITHUB_WATCH_CONFIG_DIR", "/app/config"))
    data_dir = Path(os.getenv("GITHUB_WATCH_DATA_DIR", "/data"))
    ollama_base = os.getenv("OLLAMA_BASE_URL", "").strip()
    if not ollama_base:
        ollama_base = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434").strip()
    return Settings(
        github_token=os.getenv("GITHUB_TOKEN", "").strip(),
        github_api_base_url=os.getenv("GITHUB_API_BASE_URL", "https://api.github.com").strip(),
        repos_dir=config_root / "repos",
        prompts_dir=config_root / "prompts",
        pipelines_file=config_root / "pipelines.yaml",
        data_dir=data_dir,
        poll_interval_seconds=int(os.getenv("GITHUB_WATCH_POLL_INTERVAL_SECONDS", "86400")),
        request_sleep_seconds=float(os.getenv("GITHUB_WATCH_REQUEST_SLEEP_SECONDS", "1")),
        http_timeout_seconds=int(os.getenv("GITHUB_WATCH_HTTP_TIMEOUT_SECONDS", "30")),
        max_retries=int(os.getenv("GITHUB_WATCH_MAX_RETRIES", "3")),
        log_level=os.getenv("GITHUB_WATCH_LOG_LEVEL", "INFO").strip(),
        ollama_base_url=ollama_base,
        ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5-coder:14b-instruct-q4_K_M").strip(),
        ollama_timeout_seconds=int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120")),
    )
