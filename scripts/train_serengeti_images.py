"""Fine-tune ResNet-18 on locally cached Serengeti JPEGs (predator vs non-predator)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import default_data_config
from src.data import ensure_data_dirs, load_manifest
from src.image_training import train_serengeti_predator_on_disk
from src.serengeti_image_paths import list_records_with_local_files
from src.training import TrainingConfig


def main() -> None:
    p = argparse.ArgumentParser(description="Train ResNet-18 on downloaded Serengeti images.")
    p.add_argument(
        "--images-dir",
        type=str,
        default="",
        help="Directory with JPEGs (default: data/processed/serengeti_images).",
    )
    p.add_argument("--epochs", type=int, default=5)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument(
        "--output-dir",
        type=str,
        default="results/experiments/serengeti_disk_resnet18",
    )
    p.add_argument("--val-fraction", type=float, default=0.2)
    args = p.parse_args()

    data_cfg = default_data_config()
    ensure_data_dirs(data_cfg)
    images_root = Path(args.images_dir) if args.images_dir else (data_cfg.processed_dir / "serengeti_images")

    records = load_manifest(data_cfg)
    local = list_records_with_local_files(records, images_root)
    print(f"Local images found: {len(local)} under {images_root}")
    if len(local) < 2:
        print("Download a few images first, e.g.:")
        print("  python scripts/download_serengeti_images.py --max-images 32 --split train")
        sys.exit(1)

    tcfg = TrainingConfig(
        epochs=args.epochs,
        learning_rate=args.lr,
        batch_size=args.batch_size,
        output_dir=args.output_dir,
        model_name="resnet18_serengeti_disk",
    )
    history = train_serengeti_predator_on_disk(
        records,
        images_root,
        tcfg,
        val_fraction=args.val_fraction,
        split_seed=data_cfg.split_seed,
    )
    print(f"Done. metrics -> {args.output_dir}/metrics.json")
    print(f"checkpoint -> {args.output_dir}/resnet18_serengeti_disk.pt")
    if history.get("val_acc"):
        print(f"final val_acc={history['val_acc'][-1]}")


if __name__ == "__main__":
    main()
