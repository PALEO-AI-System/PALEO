"""Train ResNet-18 on locally cached Snapshot Serengeti JPEGs (predator / not)."""

from __future__ import annotations

import json
import random
from dataclasses import asdict
from importlib import import_module
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .data import DatasetRecord
from .serengeti_image_paths import list_records_with_local_files, local_image_path
from .training import TrainingConfig, save_training_history

_TORCH_IMPORT_ERROR = ""

torch: Any | None = None
nn: Any | None = None
DataLoader: Any | None = None
transforms: Any | None = None
ResNet18_Weights: Any | None = None
resnet18: Any | None = None

try:
    torch = import_module("torch")
    nn = import_module("torch.nn")
    data_utils = import_module("torch.utils.data")
    DataLoader = data_utils.DataLoader
    transforms = import_module("torchvision.transforms")
    tv_models = import_module("torchvision.models")
    ResNet18_Weights = tv_models.ResNet18_Weights
    resnet18 = tv_models.resnet18
except ImportError as exc:  # pragma: no cover
    _TORCH_IMPORT_ERROR = str(exc)


def _require_torch_image_deps() -> tuple[Any, Any, Any, Any, Any, Any]:
    if (
        torch is None
        or nn is None
        or DataLoader is None
        or transforms is None
        or ResNet18_Weights is None
        or resnet18 is None
    ):
        msg = "Install torch and torchvision to train on images."
        if _TORCH_IMPORT_ERROR:
            msg += f" Import error: {_TORCH_IMPORT_ERROR}"
        raise RuntimeError(msg)
    return torch, nn, DataLoader, transforms, ResNet18_Weights, resnet18


def _load_pil_image_module() -> Any:
    try:
        return import_module("PIL.Image")
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Install Pillow to load local JPEGs.") from exc


class SerengetiDiskDataset:
    """Loads RGB images from disk; labels = ``predator_label`` (0/1)."""

    def __init__(
        self,
        records: List[DatasetRecord],
        images_root: Path,
        image_size: int = 224,
        augment: bool = False,
    ) -> None:
        torch_module, _, _, transforms_module, _, _ = _require_torch_image_deps()
        _ = torch_module
        self.records = records
        self.images_root = Path(images_root)

        ops: List[Any] = [
            transforms_module.Resize((image_size, image_size)),
            transforms_module.ToTensor(),
            transforms_module.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ]
        if augment:
            ops = [
                transforms_module.RandomResizedCrop(image_size, scale=(0.8, 1.0)),
                transforms_module.RandomHorizontalFlip(p=0.5),
                transforms_module.ToTensor(),
                transforms_module.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        self.transform = transforms_module.Compose(ops)

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> Tuple[Any, Any]:
        torch_module, _, _, _, _, _ = _require_torch_image_deps()
        image_module = _load_pil_image_module()

        rec = self.records[idx]
        path = local_image_path(rec, self.images_root)
        img = image_module.open(path).convert("RGB")
        x = self.transform(img)
        y = int(rec.predator_label)
        y_t = torch_module.tensor(y, dtype=torch_module.long)
        return x, y_t


def _split_train_val(
    records: List[DatasetRecord],
    val_fraction: float,
    seed: int,
) -> Tuple[List[DatasetRecord], List[DatasetRecord]]:
    if not records:
        return [], []
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


def _accuracy(logits: Any, targets: Any) -> float:
    """Batch accuracy; runs under ``no_grad`` so it is safe in the train loop."""
    torch_module, _, _, _, _, _ = _require_torch_image_deps()
    with torch_module.no_grad():
        pred = logits.argmax(dim=1)
        return float((pred == targets).float().mean().item())


def load_classifier(checkpoint_path: str | Path) -> Any:
    """Load a saved ResNet-18 checkpoint for inference."""
    torch_module, nn_module, _, _, _, resnet18_fn = _require_torch_image_deps()
    ckpt = torch_module.load(checkpoint_path, map_location="cpu")
    model = resnet18_fn(weights=None)
    model.fc = nn_module.Linear(model.fc.in_features, 2)
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    return model


def train_serengeti_predator_on_disk(
    records: List[DatasetRecord],
    images_root: Path,
    config: TrainingConfig,
    val_fraction: float = 0.15,
    split_seed: int = 42,
    image_size: int = 224,
    augment: bool = True,
) -> Dict[str, List[float]]:
    """Fine-tune ResNet-18 fc layer for binary predator classification."""
    torch_module, nn_module, data_loader_cls, _, weights_enum, resnet18_fn = (
        _require_torch_image_deps()
    )

    local = list_records_with_local_files(records, images_root)
    if len(local) < 2:
        raise RuntimeError(
            f"Need at least 2 local images under {images_root}; "
            "run scripts/download_serengeti_images.py first."
        )

    train_recs, val_recs = _split_train_val(local, val_fraction=val_fraction, seed=split_seed)
    train_ds = SerengetiDiskDataset(train_recs, images_root, image_size=image_size, augment=augment)
    val_ds = SerengetiDiskDataset(val_recs, images_root, image_size=image_size, augment=False)

    pin_memory = torch_module.cuda.is_available()
    train_loader = data_loader_cls(
        train_ds,
        batch_size=min(config.batch_size, len(train_ds)),
        shuffle=True,
        num_workers=0,
        pin_memory=pin_memory,
    )
    val_loader = data_loader_cls(
        val_ds,
        batch_size=min(config.batch_size, max(len(val_ds), 1)),
        shuffle=False,
        num_workers=0,
        pin_memory=pin_memory,
    )

    device = torch_module.device("cuda" if torch_module.cuda.is_available() else "cpu")
    weights = weights_enum.IMAGENET1K_V1
    model = resnet18_fn(weights=weights)
    model.fc = nn_module.Linear(model.fc.in_features, 2)
    model.to(device)

    crit = nn_module.CrossEntropyLoss()
    for name, param in model.named_parameters():
        if name.startswith("layer4") or name.startswith("fc"):
            param.requires_grad = True
        else:
            param.requires_grad = False
    opt = torch_module.optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=config.learning_rate,
    )

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
    torch_module.save(ckpt, out_dir / "resnet18_serengeti_disk.pt")

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
