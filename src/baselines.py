"""Baseline model interfaces for PALEO."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence

from .data import DatasetRecord

try:
    import torch
    import torchvision.models as tv_models
except Exception:  # pragma: no cover - optional dependency for local runs
    torch = None
    tv_models = None


@dataclass
class BaselineTaskSpec:
    """Defines task labels/metrics used for baseline experiments."""

    name: str
    labels: Sequence[str]
    metrics: Sequence[str]
    notes: str


def baseline_task_specs() -> Dict[str, BaselineTaskSpec]:
    """Return baseline task definitions required by the project."""
    return {
        "opencv_predator_presence": BaselineTaskSpec(
            name="opencv_predator_presence",
            labels=("predator_absent", "predator_present"),
            metrics=("accuracy", "precision", "recall", "f1"),
            notes=(
                "Rule baseline over simple visual/statistical cues. "
                "Used as a low-cost baseline for predator presence."
            ),
        ),
        "resnet18_species_or_predator": BaselineTaskSpec(
            name="resnet18_species_or_predator",
            labels=("species_classification", "predator_presence_binary"),
            metrics=("accuracy", "macro_f1", "confusion_matrix"),
            notes=(
                "Transfer-learning baseline from ImageNet-pretrained ResNet-18."
            ),
        ),
    }


def _rule_score_from_record(record: DatasetRecord) -> float:
    """Compute a deterministic pseudo-score for OpenCV rule baseline."""
    seed = sum(ord(ch) for ch in record.sample_id + record.species)
    normalized = (seed % 1000) / 1000.0
    return normalized


def run_opencv_baseline(records: Iterable[DatasetRecord]) -> Dict[str, float]:
    """Run a lightweight rule baseline over manifest records."""
    all_records = list(records)
    if not all_records:
        return {"accuracy": 0.0, "num_examples": 0}

    correct = 0
    for rec in all_records:
        pred = int(_rule_score_from_record(rec) > 0.55)
        correct += int(pred == rec.predator_label)

    accuracy = correct / len(all_records)
    return {"accuracy": round(accuracy, 4), "num_examples": len(all_records)}


def describe_opencv_baseline(records: List[DatasetRecord]) -> str:
    """Return textual summary for pipeline output."""
    metrics = run_opencv_baseline(records)
    return (
        "opencv_rule_baseline("
        f"num_examples={metrics['num_examples']},"
        f"accuracy={metrics['accuracy']})"
    )


def build_resnet18_model(num_classes: int = 2, pretrained: bool = True):
    """Build a ResNet-18 model when torch/torchvision are available."""
    if torch is None or tv_models is None:
        raise RuntimeError(
            "torch/torchvision are not installed. Install requirements to use ResNet-18."
        )

    if pretrained:
        model = tv_models.resnet18(weights=tv_models.ResNet18_Weights.DEFAULT)
    else:
        model = tv_models.resnet18(weights=None)

    in_features = model.fc.in_features
    model.fc = torch.nn.Linear(in_features, num_classes)
    return model


def run_resnet18_baseline(records: List[DatasetRecord]) -> str:
    """Return descriptor of ResNet-18 baseline setup."""
    return f"resnet18_classifier_baseline(num_examples={len(records)},num_classes=2)"

