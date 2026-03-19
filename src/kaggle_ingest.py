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


def csv_quick_stats(
    csv_path: Path,
    max_preview_rows: int = 2,
    row_count_max_file_bytes: Optional[int] = None,
) -> Dict[str, Any]:
    """Return column names, row count (excluding header), and a few preview cells.

    Streams the file so large CSVs do not load into memory. If ``row_count_max_file_bytes``
    is set and the file is larger, skip scanning all rows (``num_rows`` is ``None``) but
    still return header + preview rows — keeps ``run_pipeline`` fast when a multi-GB CSV
    is present locally.
    """
    csv_path = Path(csv_path)
    columns: List[str] = []
    row_count: Optional[int] = 0
    preview: List[List[str]] = []
    row_count_skipped = False
    try:
        file_size = csv_path.stat().st_size
    except OSError:
        file_size = -1

    skip_full_count = (
        row_count_max_file_bytes is not None
        and file_size >= 0
        and file_size > row_count_max_file_bytes
    )

    with csv_path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return {
                "path": str(csv_path.as_posix()),
                "columns": [],
                "num_columns": 0,
                "num_rows": 0,
                "preview_rows": [],
                "file_size_bytes": max(file_size, 0),
                "row_count_skipped": False,
                "error": "empty_file",
            }
        columns = [h.strip() for h in header]
        if skip_full_count:
            row_count_skipped = True
            row_count = None
            for row in reader:
                if len(preview) < max_preview_rows:
                    preview.append(row[: min(len(row), len(columns))])
                else:
                    break
        else:
            for row in reader:
                assert row_count is not None
                row_count += 1
                if len(preview) < max_preview_rows:
                    preview.append(row[: min(len(row), len(columns))])

    out: Dict[str, Any] = {
        "path": str(csv_path),
        "columns": columns,
        "num_columns": len(columns),
        "num_rows": row_count,
        "preview_rows": preview,
        "file_size_bytes": max(file_size, 0),
        "row_count_skipped": row_count_skipped,
    }
    return out


def summarize_all_kaggle(
    kaggle_root: Optional[Path] = None,
    row_count_max_file_bytes: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Summarize every CSV under the default Kaggle root."""
    root = kaggle_root or default_kaggle_root()
    return [
        csv_quick_stats(p, row_count_max_file_bytes=row_count_max_file_bytes)
        for p in iter_kaggle_csv_paths(root)
    ]


# Skip full row scan above this size for pipeline / ``--quick`` stats (keeps ``run_pipeline``
# fast when e.g. a ~15M-row accel CSV is present, while still counting medium CSVs like dino tactical).
KAGGLE_PIPELINE_ROW_COUNT_MAX_FILE_BYTES = 100 * 1024 * 1024


def summarize_kaggle_for_pipeline() -> str:
    """Compact summary line for ``run_pipeline`` (fast on huge local CSVs)."""
    summaries = summarize_all_kaggle(
        row_count_max_file_bytes=KAGGLE_PIPELINE_ROW_COUNT_MAX_FILE_BYTES,
    )
    if not summaries:
        return "kaggle_local=0_csv"
    parts: List[str] = []
    for s in summaries:
        name = Path(s["path"]).name
        if s.get("row_count_skipped"):
            parts.append(f"{name}:deferred_row_count")
        elif s.get("num_rows") is not None:
            parts.append(f"{name}:n={s['num_rows']}")
        else:
            parts.append(f"{name}:?")
    return "kaggle_local=" + ";".join(parts)
