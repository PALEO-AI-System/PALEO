"""Train ResNet-18 on locally cached Snapshot Serengeti JPEGs (predator / not)."""

from __future__ import annotations

import json
import random
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Tuple

from .data import DatasetRecord
from .serengeti_image_paths import list_records_with_local_files, local_image_path
from .training import TrainingConfig, save_training_history

_TORCH_IMPORT_ERROR = ""

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, Dataset
    from torchvision import transforms
    from torchvision.models import ResNet18_Weights, resnet18
except ImportError as exc:  # pragma: no cover
    _TORCH_IMPORT_ERROR = str(exc)
    torch = None
    nn = None
    DataLoader = None
    Dataset = object  # type: ignore[misc, assignment]
    resnet18 = None
    transforms = None


class SerengetiDiskDataset(Dataset):  # type: ignore[misc]
    """Loads RGB images from disk; labels = ``predator_label`` (0/1)."""

    def __init__(
        self,
        records: List[DatasetRecord],
        images_root: Path,
        image_size: int = 224,
        augment: bool = False,
    ) -> None:
        if torch is None:
            raise RuntimeError("torch and torchvision are required for image training.")
        self.records = records
        self.images_root = Path(images_root)
        ops: List = [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
        if augment:
            ops = [
                transforms.RandomResizedCrop(image_size, scale=(0.8, 1.0)),
                transforms.RandomHorizontalFlip(p=0.5),
            ] + ops[1:]
        self.transform = transforms.Compose(ops)

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        from PIL import Image

        rec = self.records[idx]
        path = local_image_path(rec, self.images_root)
        img = Image.open(path).convert("RGB")
        x = self.transform(img)
        y = int(rec.predator_label)
        y_t = torch.tensor(y, dtype=torch.long)
        return x, y_t


def _split_train_val(
    records: List[DatasetRecord],
    val_fraction: float,
    seed: int,
) -> Tuple[List[DatasetRecord], List[DatasetRecord]]:
    if not records:
        return [], []
    # Prefer manifest splits when both sides have at least one sample.
    train_m = [r for r in records if r.split == "train"]
    val_m = [r for r in records if r.split == "val"]
    if len(train_m) >= 1 and len(val_m) >= 1:
        return train_m, val_m
    rng = random.Random(seed)
    idxs = list(range(len(records)))
    rng.shuffle(idxs)
    n_val = max(1, int(len(records) * val_fraction))
    val_idx = set(idxs[:n_val])
    train = [records[i] for i in range(len(records)) if i not in val_idx]
    val = [records[i] for i in range(len(records)) if i in val_idx]
    if not train:
        train, val = val, train
    return train, val


def _accuracy(logits: torch.Tensor, targets: torch.Tensor) -> float:
    """Batch accuracy; runs under ``no_grad`` so it is safe in the train loop."""
    with torch.no_grad():
        pred = logits.argmax(dim=1)
        return float((pred == targets).float().mean().item())


def train_serengeti_predator_on_disk(
    records: List[DatasetRecord],
    images_root: Path,
    config: TrainingConfig,
    val_fraction: float = 0.15,
    split_seed: int = 42,
    image_size: int = 224,
) -> Dict[str, List[float]]:
    """Fine-tune ResNet-18 fc layer for binary predator classification."""
    if torch is None or resnet18 is None:
        msg = "Install torch and torchvision to train on images."
        if _TORCH_IMPORT_ERROR:
            msg += f" Import error: {_TORCH_IMPORT_ERROR}"
        raise RuntimeError(msg)

    local = list_records_with_local_files(records, images_root)
    if len(local) < 2:
        raise RuntimeError(
            f"Need at least 2 local images under {images_root}; "
            "run scripts/download_serengeti_images.py first."
        )

    train_recs, val_recs = _split_train_val(local, val_fraction=val_fraction, seed=split_seed)
    train_ds = SerengetiDiskDataset(train_recs, images_root, image_size=image_size, augment=True)
    val_ds = SerengetiDiskDataset(val_recs, images_root, image_size=image_size, augment=False)

    pin_memory = torch.cuda.is_available()
    train_loader = DataLoader(
        train_ds,
        batch_size=min(config.batch_size, len(train_ds)),
        shuffle=True,
        num_workers=0,
        pin_memory=pin_memory,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=min(config.batch_size, max(len(val_ds), 1)),
        shuffle=False,
        num_workers=0,
        pin_memory=pin_memory,
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    weights = ResNet18_Weights.IMAGENET1K_V1
    model = resnet18(weights=weights)
    model.fc = nn.Linear(model.fc.in_features, 2)
    model.to(device)

    crit = nn.CrossEntropyLoss()
    # Fine-tune last block + head; freeze earlier layers for tiny datasets.
    for name, param in model.named_parameters():
        if name.startswith("layer4") or name.startswith("fc"):
            param.requires_grad = True
        else:
            param.requires_grad = False
    opt = torch.optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=config.learning_rate)

    epochs_hist: List[int] = []
    train_losses: List[float] = []
    val_losses: List[float] = []
    val_accs: List[float] = []

    train_accs: List[float] = []
    for epoch in range(1, config.epochs + 1):
        model.train()
        running = 0.0
        n_batches = 0
        t_acc_run = 0.0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad(set_to_none=True)
            logits = model(xb)
            loss = crit(logits, yb)
            loss.backward()
            opt.step()
            running += float(loss.item())
            t_acc_run += _accuracy(logits, yb)
            n_batches += 1
        train_loss = running / max(n_batches, 1)
        train_acc_ep = t_acc_run / max(n_batches, 1)

        model.eval()
        v_loss = 0.0
        v_acc = 0.0
        n_val_batches = 0
        for xb, yb in val_loader:
            xb, yb = xb.to(device), yb.to(device)
            logits = model(xb)
            v_loss += float(crit(logits, yb).item())
            v_acc += _accuracy(logits, yb)
            n_val_batches += 1
        val_loss = v_loss / max(n_val_batches, 1)
        val_acc = v_acc / max(n_val_batches, 1)

        epochs_hist.append(epoch)
        train_losses.append(round(train_loss, 4))
        val_losses.append(round(val_loss, 4))
        val_accs.append(round(val_acc, 4))
        train_accs.append(round(train_acc_ep, 4))

    out_dir = Path(config.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ckpt = {
        "model_state": model.state_dict(),
        "config": asdict(config),
        "num_train": len(train_recs),
        "num_val": len(val_recs),
        "weights_backbone": str(weights),
        "task": "predator_binary",
    }
    torch.save(ckpt, out_dir / "resnet18_serengeti_disk.pt")

    # Align with scaffold metrics.json shape + extra fields.
    history = {
        "epochs": epochs_hist,
        "train_loss": train_losses,
        "val_loss": val_losses,
        "val_acc": val_accs,
        "train_acc": train_accs,
        "learning_rate": [config.learning_rate] * len(epochs_hist),
        "num_local_images": len(local),
        "images_root": str(Path(images_root).as_posix()),
    }
    save_training_history(history, config)
    (out_dir / "train_meta.json").write_text(
        json.dumps(
            {
                "checkpoint": "resnet18_serengeti_disk.pt",
                "num_train": len(train_recs),
                "num_val": len(val_recs),
                "final_val_acc": val_accs[-1] if val_accs else None,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return history
