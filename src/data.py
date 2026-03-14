"""Data ingestion and manifest utilities for PALEO."""

from __future__ import annotations

import csv
import hashlib
import json
import random
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from .config import DataConfig


@dataclass
class DatasetRecord:
    """Normalized sample record used by training and baselines."""

    sample_id: str
    image_path: str
    species: str
    predator_label: int
    split: str
    source: str = "snapshot_serengeti"


def ensure_data_dirs(config: DataConfig) -> None:
    """Create expected dataset directories."""
    for path in (config.root_dir, config.raw_dir, config.processed_dir, config.manifests_dir):
        path.mkdir(parents=True, exist_ok=True)


def _stable_split(sample_id: str, config: DataConfig) -> str:
    """Assign deterministic train/val/test split based on sample id."""
    seeded = f"{sample_id}:{config.split_seed}".encode("utf-8")
    value = int(hashlib.sha1(seeded).hexdigest(), 16) % 10_000 / 10_000.0
    if value < config.train_split:
        return "train"
    if value < config.train_split + config.val_split:
        return "val"
    return "test"


def _to_predator_label(species: str, config: DataConfig) -> int:
    return int(species.lower() in config.predator_species)


def _load_rows_from_csv(path: Path) -> Iterable[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


def create_manifest_from_csv(
    config: DataConfig,
    csv_path: Path,
    species_field: str = "species",
    id_field: str = "capture_id",
    image_field: str = "image_path",
) -> List[DatasetRecord]:
    """Create a normalized JSONL manifest from CSV metadata."""
    ensure_data_dirs(config)

    records: List[DatasetRecord] = []
    for idx, row in enumerate(_load_rows_from_csv(csv_path)):
        if idx >= config.max_records:
            break
        species = (row.get(species_field) or "unknown").strip().lower()
        sample_id = (row.get(id_field) or f"row_{idx}").strip()
        image_path = (row.get(image_field) or "").strip()
        record = DatasetRecord(
            sample_id=sample_id,
            image_path=image_path,
            species=species,
            predator_label=_to_predator_label(species, config),
            split=_stable_split(sample_id, config),
        )
        records.append(record)

    with config.manifest_path.open("w", encoding="utf-8") as out:
        for rec in records:
            out.write(json.dumps(asdict(rec)) + "\n")

    return records


def create_synthetic_manifest(config: DataConfig, num_records: int = 120) -> List[DatasetRecord]:
    """Create a deterministic synthetic fallback manifest for local dev/tests."""
    ensure_data_dirs(config)
    random.seed(config.split_seed)
    species_pool: Sequence[str] = (
        "lion",
        "zebra",
        "gazelle",
        "hyena_spotted",
        "buffalo",
        "wildebeest",
    )
    records: List[DatasetRecord] = []
    for idx in range(num_records):
        species = random.choice(species_pool)
        sample_id = f"synth_{idx:05d}"
        record = DatasetRecord(
            sample_id=sample_id,
            image_path=f"synthetic/{sample_id}.jpg",
            species=species,
            predator_label=_to_predator_label(species, config),
            split=_stable_split(sample_id, config),
            source="synthetic",
        )
        records.append(record)

    with config.manifest_path.open("w", encoding="utf-8") as out:
        for rec in records:
            out.write(json.dumps(asdict(rec)) + "\n")

    return records


def load_manifest(config: DataConfig) -> List[DatasetRecord]:
    """Read normalized dataset manifest from disk."""
    if not config.manifest_path.exists():
        return []
    records: List[DatasetRecord] = []
    with config.manifest_path.open("r", encoding="utf-8") as f:
        for line in f:
            payload = json.loads(line)
            records.append(DatasetRecord(**payload))
    return records


def download_reference_metadata(config: DataConfig, filename: str = "snapshot_serengeti_reference.html") -> Path:
    """Download Snapshot Serengeti reference metadata page for provenance."""
    ensure_data_dirs(config)
    target = config.raw_dir / filename
    with urllib.request.urlopen(config.snapshot_serengeti_metadata_url, timeout=20) as response:
        target.write_bytes(response.read())
    return target


def summarize_manifest(records: Sequence[DatasetRecord]) -> Dict[str, Any]:
    """Compute quick summary stats for reporting."""
    splits = {"train": 0, "val": 0, "test": 0}
    predators = 0
    species_counts: Dict[str, int] = {}
    for rec in records:
        splits[rec.split] = splits.get(rec.split, 0) + 1
        predators += rec.predator_label
        species_counts[rec.species] = species_counts.get(rec.species, 0) + 1

    return {
        "num_records": len(records),
        "num_predator": predators,
        "num_prey_or_other": max(len(records) - predators, 0),
        "splits": splits,
        "num_species": len(species_counts),
    }


def prepare_datasets(config: DataConfig, use_synthetic_fallback: bool = True) -> Dict[str, Any]:
    """Prepare manifest and return summary for downstream pipeline steps."""
    ensure_data_dirs(config)
    records = load_manifest(config)
    if not records and use_synthetic_fallback:
        records = create_synthetic_manifest(config)

    summary = summarize_manifest(records)
    return {
        "root_dir": str(config.root_dir),
        "raw_dir": str(config.raw_dir),
        "processed_dir": str(config.processed_dir),
        "manifest_path": str(config.manifest_path),
        "license_url": config.snapshot_serengeti_license_url,
        "splits": summary["splits"],
        "num_records": summary["num_records"],
        "num_species": summary["num_species"],
    }


def sample_training_batch(config: DataConfig, split: str = "train", batch_size: int = 8) -> List[DatasetRecord]:
    """Return a small deterministic batch from the manifest."""
    records = load_manifest(config)
    split_records = [rec for rec in records if rec.split == split]
    if not split_records:
        return []
    return split_records[:batch_size]


