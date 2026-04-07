"""Evaluate a trained Serengeti ResNet-18 checkpoint on local JPEGs."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import default_data_config
from src.data import DatasetRecord, load_manifest
from src.image_training import SerengetiDiskDataset, torch, resnet18, nn
from src.serengeti_image_paths import list_records_with_local_files


def _pick_eval_records(
    records: List[DatasetRecord],
    split_seed: int,
    val_fraction: float = 0.2,
) -> List[DatasetRecord]:
    val = [r for r in records if r.split == "val"]
    if val:
        return val
    idxs = list(range(len(records)))
    rng = random.Random(split_seed)
    rng.shuffle(idxs)
    n_val = max(1, int(len(records) * val_fraction))
    chosen = set(idxs[:n_val])
    return [records[i] for i in range(len(records)) if i in chosen]


def main() -> None:
    p = argparse.ArgumentParser(description="Evaluate local Serengeti image classifier.")
    p.add_argument(
        "--checkpoint",
        type=str,
        default="results/experiments/serengeti_disk_resnet18_e5_n256/resnet18_serengeti_disk.pt",
    )
    p.add_argument(
        "--images-dir",
        type=str,
        default="",
        help="Directory with downloaded JPEGs (default: data/processed/serengeti_images).",
    )
    p.add_argument(
        "--output-dir",
        type=str,
        default="results/experiments/serengeti_disk_resnet18_e5_n256/eval",
    )
    p.add_argument("--batch-size", type=int, default=16)
    args = p.parse_args()

    if torch is None or resnet18 is None or nn is None:
        raise RuntimeError("torch + torchvision are required to evaluate checkpoints.")

    from sklearn.metrics import classification_report, confusion_matrix
    from torch.utils.data import DataLoader

    cfg = default_data_config()
    images_root = Path(args.images_dir) if args.images_dir else (cfg.processed_dir / "serengeti_images")
    records = load_manifest(cfg)
    local_records = list_records_with_local_files(records, images_root)
    if len(local_records) < 2:
        raise RuntimeError("Not enough local images for eval. Download more first.")

    eval_records = _pick_eval_records(local_records, split_seed=cfg.split_seed)
    if not eval_records:
        raise RuntimeError("No eval records selected.")

    ds = SerengetiDiskDataset(eval_records, images_root, augment=False)
    loader = DataLoader(
        ds,
        batch_size=min(args.batch_size, len(ds)),
        shuffle=False,
        num_workers=0,
        pin_memory=torch.cuda.is_available(),
    )

    ckpt_path = Path(args.checkpoint)
    checkpoint = torch.load(ckpt_path, map_location="cpu")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, 2)
    model.load_state_dict(checkpoint["model_state"])
    model.to(device)
    model.eval()

    y_true: List[int] = []
    y_pred: List[int] = []
    with torch.no_grad():
        for xb, yb in loader:
            xb = xb.to(device)
            logits = model(xb)
            pred = logits.argmax(dim=1).cpu().tolist()
            y_pred.extend(int(v) for v in pred)
            y_true.extend(int(v) for v in yb.tolist())

    labels = [0, 1]
    report = classification_report(
        y_true,
        y_pred,
        labels=labels,
        target_names=["non_predator", "predator"],
        digits=4,
        output_dict=True,
        zero_division=0,
    )
    cm = confusion_matrix(y_true, y_pred, labels=labels).tolist()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "checkpoint": str(ckpt_path.as_posix()),
        "num_eval_images": len(eval_records),
        "images_root": str(images_root.as_posix()),
        "confusion_matrix_labels": ["non_predator", "predator"],
        "confusion_matrix": cm,
        "classification_report": report,
    }
    (out_dir / "eval_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"eval_images={len(eval_records)}")
    print(f"accuracy={report.get('accuracy', 0.0):.4f}")
    print(f"macro_f1={report.get('macro avg', {}).get('f1-score', 0.0):.4f}")
    print(f"saved={out_dir / 'eval_metrics.json'}")


if __name__ == "__main__":
    main()
