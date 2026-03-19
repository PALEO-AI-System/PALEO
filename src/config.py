"""Configuration objects for PALEO."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Tuple


@dataclass
class DataConfig:
    """Settings for dataset ingestion and manifest creation."""

    root_dir: Path
    raw_dir: Path
    processed_dir: Path
    manifests_dir: Path
    snapshot_serengeti_metadata_url: str
    snapshot_serengeti_license_url: str
    predator_species: Tuple[str, ...]
    train_split: float
    val_split: float
    test_split: float
    split_seed: int
    manifest_name: str = "serengeti_manifest.jsonl"
    max_records: int = 500

    def validate_splits(self) -> None:
        """Raise if train/val/test are invalid."""
        total = self.train_split + self.val_split + self.test_split
        if abs(total - 1.0) > 1e-6:
            raise ValueError("Train/val/test splits must sum to 1.0")

    @property
    def manifest_path(self) -> Path:
        """Path to the processed manifest JSONL."""
        return self.manifests_dir / self.manifest_name


@dataclass
class PotConfig:
    """Runtime assumptions for Path of Titans integration."""

    target_window_title: str = "Path of Titans"
    capture_region: Tuple[int, int, int, int] = (0, 0, 1280, 720)
    target_fps: int = 8
    emergency_stop_key: str = "f12"
    keymap: Dict[str, Tuple[str, ...]] = field(
        default_factory=lambda: {
            # Locomotion
            "FLEE": ("shift", "w"),
            "GRAZE": ("w",),
            "FOLLOW_HERD": ("w", "a"),
            "HOLD_POSITION": (),
            "EXPLORE": ("w",),
            # Calls (mapped to vocal wheel slots by future config)
            "CALL_FRIENDLY": ("1",),
            "CALL_THREATEN": ("2",),
            "CALL_DANGER": ("3",),
            # Survival
            "SEEK_WATER": ("w",),
            "FORAGE": ("w",),
        }
    )


@dataclass
class LettaConfig:
    """Basic Letta integration settings."""

    integration_mode: str = "python_tools"
    host: str = "127.0.0.1"
    port: int = 8000
    enable_http_api: bool = False


def default_data_config() -> DataConfig:
    """Return default dataset settings for local execution."""
    project_root = Path(__file__).resolve().parents[1]
    data_root = project_root / "data"
    # Snapshot Serengeti consensus CSV uses camelCase species names (e.g., lionFemale),
    # so we keep the list aligned to those actual string values.
    predator_species = (
        "lionfemale",
        "lionmale",
        "cheetah",
        "leopard",
        "hyenaspotted",
        "hyenastriped",
        "jackal",
        "wildcat",
    )

    cfg = DataConfig(
        root_dir=data_root,
        raw_dir=data_root / "raw",
        processed_dir=data_root / "processed",
        manifests_dir=data_root / "manifests",
        snapshot_serengeti_metadata_url=(
            "https://lila.science/datasets/snapshot-serengeti-addendum/"
        ),
        snapshot_serengeti_license_url="https://lila.science/datasets/snapshot-serengeti/",
        predator_species=predator_species,
        train_split=0.6,
        val_split=0.2,
        test_split=0.2,
        split_seed=42,
    )
    cfg.validate_splits()
    return cfg


def default_pot_config() -> PotConfig:
    """Return conservative default PoT runtime settings."""
    return PotConfig()


def default_letta_config() -> LettaConfig:
    """Return default Letta tool orchestration settings."""
    return LettaConfig()

