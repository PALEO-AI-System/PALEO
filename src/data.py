"""Data pipeline stubs for PALEO.

These functions are placeholders for:
- dataset download
- preprocessing and split creation
- batch loading

They currently only log their intent and return simple dummy structures.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .config import DataConfig


def prepare_datasets(config: DataConfig) -> Dict[str, Any]:
    """Simulate dataset preparation and return a summary dict.

    No network or filesystem operations are performed yet.
    """
    return {
        "root_dir": str(config.root_dir),
        "sources": {
            "snapshot_serengeti": config.snapshot_serengeti_url,
            "predator_prey": config.predator_prey_search_url,
        },
        "splits": {
            "train": config.train_split,
            "val": config.val_split,
            "test": config.test_split,
        },
    }


def sample_training_batch() -> List[str]:
    """Return a dummy 'batch' description list.

    This stands in for real tensors/records that will be added later.
    """
    return ["dummy_image_1", "dummy_image_2"]

