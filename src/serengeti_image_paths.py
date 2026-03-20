"""Map Snapshot Serengeti manifest rows to locally downloaded image filenames."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import List
from urllib.parse import urlparse

from .data import DatasetRecord


def _suffix_from_url(url: str) -> str:
    path = urlparse(url).path
    suf = Path(path).suffix.lower()
    if suf in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        return suf
    return ".jpg"


def serengeti_local_filename(sample_id: str, image_url: str) -> str:
    """Same naming rule as ``scripts/download_serengeti_images.py`` (must stay in sync)."""
    digest = hashlib.sha256(f"{sample_id}:{image_url}".encode("utf-8")).hexdigest()[:12]
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in sample_id)[:64]
    return f"{safe}_{digest}{_suffix_from_url(image_url)}"


def local_image_path(record: DatasetRecord, images_root: Path) -> Path:
    """Absolute path where a downloaded Serengeti JPEG for this record should live."""
    root = Path(images_root)
    return root / serengeti_local_filename(record.sample_id, record.image_path)


def list_records_with_local_files(
    records: List[DatasetRecord],
    images_root: Path,
) -> List[DatasetRecord]:
    """Keep manifest rows whose ``image_path`` is HTTP and file exists under ``images_root``."""
    root = Path(images_root)
    out: List[DatasetRecord] = []
    for rec in records:
        if not rec.image_path.strip().lower().startswith("http"):
            continue
        path = local_image_path(rec, root)
        if path.is_file():
            out.append(rec)
    return out
