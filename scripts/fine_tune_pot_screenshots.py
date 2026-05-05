"""
Fine-tune the best Serengeti ResNet-18 checkpoint on labeled Path of Titans screenshots.

Expected dataset layout:
  data/processed/pot_screenshots_300/images/<files...>
  data/processed/pot_screenshots_300/labels.csv   (filename,label)

Binary labels:
  predator -> class 1
  non_predator -> class 0

Outputs:
  results/pot_finetune/<run_name>/
    - resnet18_pot_finetuned.pt
    - metrics.json
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.image_training import _require_torch_image_deps, load_classifier


@dataclass
class Sample:
    path: Path
    y: int


def load_labeled_samples(images_dir: Path, labels_csv: Path) -> List[Sample]:
    rows: List[Tuple[str, str]] = []
    with labels_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            fn = (r.get("filename") or "").strip()
            lab = (r.get("label") or "").strip()
            if not fn:
                continue
            if lab not in ("predator", "non_predator"):
                continue
            y = 1 if lab == "predator" else 0
            rows.append((fn, lab))

    samples: List[Sample] = []
    for fn, lab in rows:
        p = images_dir / fn
        if not p.exists():
            continue
        samples.append(Sample(path=p, y=(1 if lab == "predator" else 0)))
    return samples


class PotLabeledDataset:
    def __init__(self, samples: List[Sample], image_size: int = 224, augment: bool = True):
        torch, _, _, transforms, _, _ = _require_torch_image_deps()
        from PIL import Image

        self.samples = samples
        self.torch = torch
        self.Image = Image

        ops = [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
        if augment:
            ops = [
                transforms.RandomResizedCrop(image_size, scale=(0.85, 1.0)),
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        self.transform = transforms.Compose(ops)

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        s = self.samples[idx]
        img = self.Image.open(s.path).convert("RGB")
        x = self.transform(img)
        y = self.torch.tensor(s.y, dtype=self.torch.long)
        return x, y


def split_train_val(samples: List[Sample], val_fraction: float, seed: int) -> Tuple[List[Sample], List[Sample]]:
    rng = random.Random(seed)
    idxs = list(range(len(samples)))
    rng.shuffle(idxs)
    n_val = max(1, int(len(samples) * val_fraction))
    val = [samples[i] for i in idxs[:n_val]]
    train = [samples[i] for i in idxs[n_val:]]
    return train, val


def evaluate(model, loader, device) -> float:
    torch, _, _, _, _, _ = _require_torch_image_deps()
    correct = 0
    total = 0
    model.eval()
    with torch.no_grad():
        for xb, yb in loader:
            xb = xb.to(device)
            yb = yb.to(device)
            logits = model(xb)
            pred = logits.argmax(dim=1)
            correct += int((pred == yb).sum().item())
            total += int(yb.numel())
    return float(correct / total) if total else 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--images-dir", type=str, default="data/processed/pot_screenshots_300/images")
    parser.add_argument("--labels-csv", type=str, default="data/processed/pot_screenshots_300/labels.csv")
    parser.add_argument(
        "--base-checkpoint",
        type=str,
        default="results/experiments/resnet18_lrie4_aug_e15/resnet18_serengeti_disk.pt",
    )
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--val-fraction", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--run-name", type=str, default="pot_300_finetune")
    parser.add_argument(
        "--predator-class-weight",
        type=float,
        default=1.0,
        help="Weight multiplier for predator class (class 1) in CrossEntropyLoss.",
    )
    parser.add_argument(
        "--non-predator-class-weight",
        type=float,
        default=1.0,
        help="Weight multiplier for non_predator class (class 0) in CrossEntropyLoss.",
    )
    args = parser.parse_args()

    images_dir = Path(args.images_dir)
    labels_csv = Path(args.labels_csv)
    base_ckpt = Path(args.base_checkpoint)
    out_dir = Path("results") / "pot_finetune" / args.run_name
    out_dir.mkdir(parents=True, exist_ok=True)

    samples = load_labeled_samples(images_dir, labels_csv)
    if len(samples) < 20:
        raise SystemExit(f"Not enough labeled samples found (need >=20). Found: {len(samples)}")

    train_samples, val_samples = split_train_val(samples, val_fraction=args.val_fraction, seed=args.seed)
    if not train_samples or not val_samples:
        raise SystemExit("Train/val split failed (empty split).")

    torch, nn, DataLoader, _, _, _ = _require_torch_image_deps()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = load_classifier(base_ckpt)
    model.to(device)

    train_ds = PotLabeledDataset(train_samples, augment=True)
    val_ds = PotLabeledDataset(val_samples, augment=False)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False)

    # Fine-tune all layers with a small LR.
    opt = torch.optim.AdamW(model.parameters(), lr=float(args.learning_rate))
    class_weights = torch.tensor(
        [float(args.non_predator_class_weight), float(args.predator_class_weight)],
        dtype=torch.float32,
        device=device,
    )
    loss_fn = nn.CrossEntropyLoss(weight=class_weights)

    history = {"train_loss": [], "val_acc": []}
    for epoch in range(1, int(args.epochs) + 1):
        model.train()
        running = 0.0
        n = 0
        for xb, yb in train_loader:
            xb = xb.to(device)
            yb = yb.to(device)
            opt.zero_grad(set_to_none=True)
            logits = model(xb)
            loss = loss_fn(logits, yb)
            loss.backward()
            opt.step()
            running += float(loss.item()) * int(yb.size(0))
            n += int(yb.size(0))
        train_loss = running / max(1, n)
        val_acc = evaluate(model, val_loader, device)
        history["train_loss"].append(round(train_loss, 6))
        history["val_acc"].append(round(val_acc, 6))
        print(f"epoch={epoch} train_loss={train_loss:.4f} val_acc={val_acc:.4f}")

    ckpt_out = out_dir / "resnet18_pot_finetuned.pt"
    torch.save({"model_state_dict": model.state_dict()}, ckpt_out)

    metrics = {
        "run_name": args.run_name,
        "num_total": len(samples),
        "num_train": len(train_samples),
        "num_val": len(val_samples),
        "epochs": int(args.epochs),
        "batch_size": int(args.batch_size),
        "learning_rate": float(args.learning_rate),
        "base_checkpoint": str(base_ckpt).replace("\\", "/"),
        "class_weights": {
            "non_predator": float(args.non_predator_class_weight),
            "predator": float(args.predator_class_weight),
        },
        "final_val_acc": history["val_acc"][-1] if history["val_acc"] else None,
        "history": history,
    }
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Saved checkpoint: {ckpt_out}")
    print(f"Saved metrics: {out_dir / 'metrics.json'}")


if __name__ == "__main__":
    main()
