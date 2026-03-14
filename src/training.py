"""Training-loop stubs for PALEO.

This module sketches the interfaces needed for:
- recording convergence curves
- tracking hyperparameter settings

No real models or optimization are performed yet.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class TrainingConfig:
    epochs: int = 3
    learning_rate: float = 1e-3
    batch_size: int = 32


def default_training_config() -> TrainingConfig:
    """Return a small default training configuration."""
    return TrainingConfig()


def run_training_loop(config: TrainingConfig) -> Dict[str, List[float]]:
    """Return a dummy convergence history for loss/accuracy.

    Values are hard-coded placeholders for now.
    """
    epochs = list(range(1, config.epochs + 1))
    # Simple monotonic dummy curves
    train_loss = [1.0 / e for e in epochs]
    val_loss = [1.1 / e for e in epochs]
    train_acc = [0.5 + 0.1 * (e - 1) for e in epochs]
    val_acc = [0.45 + 0.1 * (e - 1) for e in epochs]

    return {
        "epochs": epochs,
        "train_loss": train_loss,
        "val_loss": val_loss,
        "train_acc": train_acc,
        "val_acc": val_acc,
        "learning_rate": [config.learning_rate] * len(epochs),
    }

