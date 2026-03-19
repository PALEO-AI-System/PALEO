"""Data ingestion and manifest utilities for PALEO."""

from __future__ import annotations

import csv
import hashlib
import json
import random
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

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


def _pick_row_value(row: Mapping[str, str], candidates: Sequence[str], default: str = "") -> str:
    """Pick the first matching value from `row` using case-insensitive header names."""
    if not row:
        return default
    lower_to_actual = {k.lower(): k for k in row.keys()}
    for cand in candidates:
        actual_key = lower_to_actual.get(cand.lower())
        if actual_key is not None:
            val = row.get(actual_key)
            if val is not None:
                stripped = str(val).strip()
                if stripped != "":
                    return stripped
    return default


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
        species = _pick_row_value(
            row,
            candidates=(species_field, "species", "Species", "specie"),
            default="unknown",
        ).lower()
        sample_id = _pick_row_value(
            row,
            candidates=(id_field, "capture_id", "CaptureEventID", "CaptureEventId", "captureeventid", "capture_event_id"),
            default=f"row_{idx}",
        )
        image_path = _pick_row_value(
            row,
            candidates=(
                image_field,
                "URL_Info",
                "url_info",
                "Image",
                "image_path",
                "imagePath",
            ),
            default="",
        )
        record = DatasetRecord(
            sample_id=sample_id,
            image_path=image_path,
            species=species,
            predator_label=_to_predator_label(species, config),
            split=_stable_split(sample_id, config),
            source=csv_path.stem,
        )
        records.append(record)

    # If we are ingesting Dryad Snapshot Serengeti CSVs, they may not include
    # image URLs directly (e.g., consensus_data.csv). In that case, join with
    # all_images.csv by CaptureEventID to populate image_path.
    if csv_path.stem.lower() == "consensus_data":
        # Prefer a sibling `all_images.csv` if the user organized data as `data/raw/dryad/...`.
        join_candidates = [csv_path.parent / "all_images.csv", config.raw_dir / "all_images.csv"]
        join_path = next((p for p in join_candidates if p.exists()), None)
        if join_path is not None:
            capture_ids = {rec.sample_id for rec in records if rec.image_path.strip() == ""}
            if capture_ids:
                mapping: Dict[str, str] = {}
                # URL_Info is a path fragment; we turn it into a full URL.
                base_url = "https://snapshotserengeti.s3.msi.umn.edu/"
                with join_path.open("r", encoding="utf-8", newline="") as f:
                    reader = csv.DictReader(f)
                    for row_idx, row in enumerate(reader):
                        if len(mapping) >= len(capture_ids):
                            break
                        cid = _pick_row_value(
                            row,
                            candidates=("CaptureEventID", "captureeventid"),
                            default="",
                        )
                        if cid not in capture_ids:
                            continue
                        url_info = _pick_row_value(
                            row,
                            candidates=("URL_Info", "url_info"),
                            default="",
                        )
                        if url_info:
                            mapping[cid] = base_url + str(url_info).lstrip("/")

                # Write joined URLs back to the manifest records.
                if mapping:
                    for rec in records:
                        if rec.image_path.strip() == "" and rec.sample_id in mapping:
                            rec.image_path = mapping[rec.sample_id]

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


def _stable_hash_int(value: str, seed: int) -> int:
    """Deterministic hash -> int for repeatable sampling."""
    payload = f"{value}:{seed}".encode("utf-8")
    return int(hashlib.sha1(payload).hexdigest(), 16)


def sample_training_batch(
    config: DataConfig,
    split: str = "train",
    batch_size: int = 8,
) -> List[DatasetRecord]:
    """Return a deterministic, distribution-friendly batch from the manifest.

    Instead of taking the first N rows (which can bias toward early CSV rows),
    we sort by a stable hash and take the first N. This makes dataset samples
    more representative and keeps demo metrics consistent.
    """
    records = load_manifest(config)
    split_records = [rec for rec in records if rec.split == split]
    if not split_records:
        return []
    ordered = sorted(
        split_records,
        key=lambda r: _stable_hash_int(r.sample_id, config.split_seed),
    )
    return ordered[:batch_size]


