from __future__ import annotations

import os
import socket
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


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


def _is_running_in_container() -> bool:
    if os.path.exists("/.dockerenv"):
        return True
    try:
        cgroup_text = Path("/proc/1/cgroup").read_text(encoding="utf-8")
    except OSError:
        return False
    return "docker" in cgroup_text or "containerd" in cgroup_text


def _is_url_reachable(base_url: str, timeout_seconds: float = 0.3) -> bool:
    parsed = urlparse(base_url)
    host = parsed.hostname
    if not host:
        return False
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True
    except OSError:
        return False


def _resolve_ollama_base_url() -> str:
    explicit_base = os.getenv("OLLAMA_BASE_URL", "").strip()
    if explicit_base:
        return explicit_base

    # Backward-compatible alias; keep as highest-priority fallback after OLLAMA_BASE_URL.
    alias_host = os.getenv("OLLAMA_HOST", "").strip()
    if alias_host:
        return alias_host

    # Auto-detect best default for host-run vs container-run.
    candidates = ["http://127.0.0.1:11434", "http://localhost:11434"]
    if _is_running_in_container():
        candidates = ["http://host.docker.internal:11434", *candidates]

    for candidate in candidates:
        if _is_url_reachable(candidate):
            return candidate

    # Keep deterministic fallback even when Ollama is currently down.
    return "http://host.docker.internal:11434" if _is_running_in_container() else "http://127.0.0.1:11434"


def load_settings() -> Settings:
    config_root = Path(os.getenv("GITHUB_WATCH_CONFIG_DIR", "/app/config"))
    data_dir = Path(os.getenv("GITHUB_WATCH_DATA_DIR", "/data"))
    ollama_base = _resolve_ollama_base_url()
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
