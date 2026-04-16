from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

from app.utils import write_text


def export_markdown(report_dir: Path, generated_at: dt.datetime, filename: str, content: str) -> Path:
    path = report_dir / filename
    write_text(path, content)
    return path


def export_domain_markdown(report_root: Path, domain: str, generated_at: dt.datetime, content: str) -> Path:
    target_dir = report_root / domain
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{generated_at.strftime('%Y-%m-%d')}-{domain}.md"
    return export_markdown(target_dir, generated_at, filename, content)
