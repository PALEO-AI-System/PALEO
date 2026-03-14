"""Lightweight model registry for PALEO artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def _registry_root() -> Path:
    return Path(__file__).resolve().parents[1] / "models"


def ensure_registry_dirs() -> Path:
    """Create model registry root if it doesn't exist."""
    root = _registry_root()
    root.mkdir(parents=True, exist_ok=True)
    return root


def register_model(task_name: str, model_path: str, metadata: Dict[str, str]) -> Path:
    """Write model metadata sidecar for a task."""
    root = ensure_registry_dirs()
    task_dir = root / task_name
    task_dir.mkdir(parents=True, exist_ok=True)
    record_path = task_dir / "latest.json"
    payload = {"task_name": task_name, "model_path": model_path, "metadata": metadata}
    record_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return record_path


def load_latest_model(task_name: str) -> Dict[str, str]:
    """Load latest model metadata for a task."""
    path = _registry_root() / task_name / "latest.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def list_tasks() -> List[str]:
    """List registry task folders."""
    root = _registry_root()
    if not root.exists():
        return []
    return sorted([p.name for p in root.iterdir() if p.is_dir()])
