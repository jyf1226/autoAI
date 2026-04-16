from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)


def export_training_samples(normalized_items: list[dict[str, Any]], training_dir: Path) -> None:
    training_dir.mkdir(parents=True, exist_ok=True)
    path = training_dir / "placeholder.jsonl"
    if not path.exists():
        path.write_text("", encoding="utf-8")
    LOGGER.info("Training exporter is stubbed; placeholder file ensured at %s", path)
