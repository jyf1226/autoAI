from __future__ import annotations

import datetime as dt
import json
import logging
from pathlib import Path
from typing import Any

import yaml

from app.models import DomainConfig, RepoTarget

LOGGER = logging.getLogger(__name__)

DOMAIN_NAMES = ["games", "image-processing", "short-video", "finance", "infra"]


def ensure_runtime_dirs(base_data_dir: Path) -> dict[str, Any]:
    raw_root = base_data_dir / "raw"
    normalized_root = base_data_dir / "normalized"
    reports_root = base_data_dir / "reports"
    state_root = base_data_dir / "state"
    embeddings_root = base_data_dir / "embeddings"
    training_root = base_data_dir / "training-samples"
    for folder in [raw_root, normalized_root, reports_root, state_root, embeddings_root, training_root]:
        folder.mkdir(parents=True, exist_ok=True)
    report_dirs = {
        "root": reports_root,
        "daily": reports_root / "daily",
        "weekly": reports_root / "weekly",
        "by-domain": reports_root / "by-domain",
    }
    for folder in report_dirs.values():
        folder.mkdir(parents=True, exist_ok=True)
    domain_dirs = {"raw": {}, "normalized": {}}
    for domain in DOMAIN_NAMES:
        domain_dirs["raw"][domain] = raw_root / domain
        domain_dirs["normalized"][domain] = normalized_root / domain
        domain_dirs["raw"][domain].mkdir(parents=True, exist_ok=True)
        domain_dirs["normalized"][domain].mkdir(parents=True, exist_ok=True)
    return {
        "raw": raw_root,
        "normalized": normalized_root,
        "reports": report_dirs,
        "state": state_root,
        "embeddings": embeddings_root,
        "training-samples": training_root,
        "domains": domain_dirs,
    }


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def to_iso(ts: dt.datetime) -> str:
    return ts.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def from_iso(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        LOGGER.warning("Load json failed for %s: %s", path, exc)
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def load_text(path: Path, default: str = "") -> str:
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8")


def load_domain_configs(repos_dir: Path) -> list[DomainConfig]:
    configs: list[DomainConfig] = []
    if not repos_dir.exists():
        raise FileNotFoundError(f"Repos config directory not found: {repos_dir}")
    for path in sorted(repos_dir.glob("*.yaml")):
        cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        domain = str(cfg.get("domain", "")).strip()
        groups = cfg.get("groups", {})
        if not domain or not isinstance(groups, dict):
            LOGGER.warning("Skip invalid repo config file: %s", path)
            continue
        targets: list[RepoTarget] = []
        for group_name, repos in groups.items():
            if not isinstance(repos, list):
                continue
            for repo_ref in repos:
                if not isinstance(repo_ref, str) or "/" not in repo_ref:
                    LOGGER.warning("Skip invalid repo ref in %s: %s", path.name, repo_ref)
                    continue
                owner, repo = repo_ref.split("/", 1)
                targets.append(RepoTarget(domain=domain, group=group_name, owner=owner, repo=repo))
        configs.append(DomainConfig(domain=domain, source_file=path.name, targets=targets))
    return configs
