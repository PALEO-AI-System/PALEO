"""Configuration objects for PALEO.

This module only defines lightweight, hard-coded defaults for now.
Later it can be extended to read from files or CLI flags.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class DataConfig:
    root_dir: Path
    snapshot_serengeti_url: str
    predator_prey_search_url: str
    train_split: float
    val_split: float
    test_split: float


def default_data_config() -> DataConfig:
    """Return a default data configuration."""
    project_root = Path(__file__).resolve().parents[1]
    data_root = project_root / "data"

    return DataConfig(
        root_dir=data_root,
        snapshot_serengeti_url="https://lila.science/datasets/snapshot-serengeti",
        predator_prey_search_url=(
            "https://www.kaggle.com/datasets?search=predator+prey+animals"
        ),
        train_split=0.6,
        val_split=0.2,
        test_split=0.2,
    )

