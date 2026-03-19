"""Scan and summarize Kaggle datasets placed under data/raw/kaggle/."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional


def default_kaggle_root(project_root: Optional[Path] = None) -> Path:
    root = project_root or Path(__file__).resolve().parents[1]
    return root / "data" / "raw" / "kaggle"


def iter_kaggle_csv_paths(kaggle_root: Path) -> List[Path]:
    """Return sorted paths to CSV files under kaggle_root (recursive)."""
    if not kaggle_root.is_dir():
        return []
    out: List[Path] = []
    for path in sorted(kaggle_root.rglob("*.csv")):
        if path.is_file():
            out.append(path)
    return out


def csv_quick_stats(csv_path: Path, max_preview_rows: int = 2) -> Dict[str, Any]:
    """Return column names, row count (excluding header), and a few preview cells.

    Streams the file so large CSVs do not load into memory.
    """
    csv_path = Path(csv_path)
    columns: List[str] = []
    row_count = 0
    preview: List[List[str]] = []

    with csv_path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return {
                "path": str(csv_path.as_posix()),
                "columns": [],
                "num_rows": 0,
                "preview_rows": [],
                "error": "empty_file",
            }
        columns = [h.strip() for h in header]
        for row in reader:
            row_count += 1
            if len(preview) < max_preview_rows:
                preview.append(row[: min(len(row), len(columns))])

    return {
        "path": str(csv_path),
        "columns": columns,
        "num_columns": len(columns),
        "num_rows": row_count,
        "preview_rows": preview,
    }


def summarize_all_kaggle(kaggle_root: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Summarize every CSV under the default Kaggle root."""
    root = kaggle_root or default_kaggle_root()
    return [csv_quick_stats(p) for p in iter_kaggle_csv_paths(root)]
