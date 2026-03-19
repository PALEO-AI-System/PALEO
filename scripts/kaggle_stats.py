"""Print column names and row counts for CSVs under data/raw/kaggle/."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.kaggle_ingest import (
    KAGGLE_PIPELINE_ROW_COUNT_MAX_FILE_BYTES,
    default_kaggle_root,
    iter_kaggle_csv_paths,
    summarize_all_kaggle,
)


def main() -> None:
    p = argparse.ArgumentParser(description="Summarize local Kaggle CSV drops (no download).")
    p.add_argument(
        "--kaggle-root",
        type=str,
        default="",
        help="Override root (default: data/raw/kaggle).",
    )
    p.add_argument(
        "--quick",
        action="store_true",
        help=(
            f"Skip full row count for CSVs larger than "
            f"{KAGGLE_PIPELINE_ROW_COUNT_MAX_FILE_BYTES // (1024 * 1024)} MB (faster; for huge files)."
        ),
    )
    p.add_argument("--json", action="store_true", help="Emit JSON instead of plain text.")
    args = p.parse_args()

    root = Path(args.kaggle_root) if args.kaggle_root else default_kaggle_root()
    paths = iter_kaggle_csv_paths(root)
    if not paths:
        msg = f"No CSV files found under {root.as_posix()}."
        if args.json:
            print(json.dumps({"error": msg, "paths": []}))
        else:
            print(msg)
            print("Add Kaggle extracts there (see docs/project_brief.md).")
        return

    threshold = KAGGLE_PIPELINE_ROW_COUNT_MAX_FILE_BYTES if args.quick else None
    summaries = summarize_all_kaggle(root, row_count_max_file_bytes=threshold)
    if args.json:
        print(json.dumps(summaries, indent=2))
        return

    for s in summaries:
        rel = Path(s["path"]).as_posix()
        print(rel)
        if s.get("row_count_skipped"):
            print(
                f"  rows: (deferred; file {s['file_size_bytes']} B — omit --quick for full count)  "
                f"cols: {s['num_columns']}"
            )
        else:
            print(f"  rows: {s['num_rows']}  cols: {s['num_columns']}")
        print(f"  columns: {', '.join(s['columns'][:12])}{' ...' if len(s['columns']) > 12 else ''}")
        if s.get("preview_rows"):
            print(f"  preview: {s['preview_rows'][0][:6] if s['preview_rows'][0] else []}")


if __name__ == "__main__":
    main()
