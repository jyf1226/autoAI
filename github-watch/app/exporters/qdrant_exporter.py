from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)


def export_to_qdrant(normalized_items: list[dict[str, Any]], embeddings_dir: Path) -> None:
    embeddings_dir.mkdir(parents=True, exist_ok=True)
    LOGGER.info("Qdrant exporter is stubbed; skip export for %s normalized items", len(normalized_items))
