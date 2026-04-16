from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any


def ensure_runtime_dirs(base_data_dir: Path) -> dict[str, Path]:
    paths = {
        "raw": base_data_dir / "raw",
        "normalized": base_data_dir / "normalized",
        "reports": base_data_dir / "reports",
        "state": base_data_dir / "state",
    }
    for folder in paths.values():
        folder.mkdir(parents=True, exist_ok=True)
    return paths


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
    except Exception:
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
import json
import logging
from pathlib import Path

import yaml

from app.models import RepoTarget

LOGGER = logging.getLogger(__name__)


def ensure_data_dirs(data_dir: Path) -> dict[str, Path]:
    targets = {
        "raw": data_dir / "raw",
        "normalized": data_dir / "normalized",
        "reports": data_dir / "reports",
        "state": data_dir / "state",
    }
    for p in targets.values():
        p.mkdir(parents=True, exist_ok=True)
    return targets


def save_json(path: Path, data: object) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_state(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except Exception as exc:
        LOGGER.warning("Load state failed (%s), fallback to empty state", exc)
    return {}


def save_state(path: Path, state: dict[str, str]) -> None:
    save_json(path, state)


def load_repo_targets(config_path: Path) -> list[RepoTarget]:
    with config_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    groups = cfg.get("groups", {})
    if not isinstance(groups, dict) or not groups:
        raise ValueError(f"groups is empty in {config_path}")

    targets: list[RepoTarget] = []
    for group, repos in groups.items():
        if not isinstance(repos, list):
            continue
        for item in repos:
            if not isinstance(item, str) or "/" not in item:
                LOGGER.warning("Skip invalid repo item in group %s: %s", group, item)
                continue
            owner, repo = item.split("/", 1)
            targets.append(RepoTarget(group=group, owner=owner, repo=repo))
    return targets
