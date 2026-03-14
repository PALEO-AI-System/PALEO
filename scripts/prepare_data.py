"""Prepare dataset manifest for PALEO."""

from pathlib import Path
import argparse
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import default_data_config
from src.data import create_manifest_from_csv, create_synthetic_manifest, summarize_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare PALEO dataset manifest.")
    parser.add_argument(
        "--csv",
        type=str,
        default="",
        help="Optional CSV metadata path. If omitted, uses synthetic fallback.",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=None,
        help="Override max records for manifest creation.",
    )
    args = parser.parse_args()

    config = default_data_config()
    if args.max_records is not None:
        config.max_records = args.max_records

    if args.csv:
        csv_path = Path(args.csv)
        records = create_manifest_from_csv(config, csv_path)
    else:
        records = create_synthetic_manifest(config)

    summary = summarize_manifest(records)
    print(f"Manifest written to: {config.manifest_path}")
    print(f"Summary: {summary}")


if __name__ == "__main__":
    main()
