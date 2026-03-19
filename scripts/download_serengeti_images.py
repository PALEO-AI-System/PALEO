"""Download a subset of Snapshot Serengeti images from manifest URLs."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import List
from urllib.parse import urlparse
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import default_data_config
from src.data import DatasetRecord, ensure_data_dirs, load_manifest


def _stable_hash_key(sample_id: str, seed: int) -> int:
    payload = f"{sample_id}:{seed}".encode("utf-8")
    return int(hashlib.sha1(payload).hexdigest(), 16)


def _suffix_from_url(url: str) -> str:
    path = urlparse(url).path
    suf = Path(path).suffix.lower()
    if suf in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        return suf
    return ".jpg"


def _safe_filename(sample_id: str, url: str) -> str:
    digest = hashlib.sha256(f"{sample_id}:{url}".encode("utf-8")).hexdigest()[:12]
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in sample_id)[:64]
    return f"{safe}_{digest}{_suffix_from_url(url)}"


def _candidate_records(config, split: str | None) -> List[DatasetRecord]:
    records = load_manifest(config)
    http_recs = [r for r in records if r.image_path.strip().lower().startswith("http")]
    if split:
        http_recs = [r for r in http_recs if r.split == split]
    return sorted(http_recs, key=lambda r: _stable_hash_key(r.sample_id, config.split_seed))


def download_image(url: str, dest: Path, timeout: int = 60) -> None:
    req = Request(
        url,
        headers={"User-Agent": "PALEO-image-fetch/1.0"},
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(req, timeout=timeout) as resp:
        dest.write_bytes(resp.read())


def main() -> None:
    p = argparse.ArgumentParser(description="Download Serengeti images listed in the JSONL manifest.")
    p.add_argument("--manifest", type=str, default="", help="Override manifest JSONL path.")
    p.add_argument(
        "--out-dir",
        type=str,
        default="",
        help="Output directory (default: data/processed/serengeti_images).",
    )
    p.add_argument("--max-images", type=int, default=8, help="Max images to download.")
    p.add_argument(
        "--split",
        type=str,
        default="",
        choices=["", "train", "val", "test"],
        help="Optional split filter (empty = any split).",
    )
    p.add_argument("--dry-run", action="store_true", help="List URLs without downloading.")
    args = p.parse_args()

    config = default_data_config()
    if args.manifest:
        from dataclasses import replace

        mp = Path(args.manifest)
        config = replace(config, manifests_dir=mp.parent, manifest_name=mp.name)

    out = Path(args.out_dir) if args.out_dir else (config.processed_dir / "serengeti_images")
    ensure_data_dirs(config)

    split = args.split or None
    candidates = _candidate_records(config, split)
    picked = candidates[: max(0, args.max_images)]

    if not picked:
        print(
            "No HTTP image URLs found in manifest (run prepare_data on Dryad CSVs first, "
            "or lower --split constraints)."
        )
        return

    print(f"Selected {len(picked)} of {len(candidates)} candidate rows (cap {args.max_images}).")
    for rec in picked:
        dest = out / _safe_filename(rec.sample_id, rec.image_path)
        print(f"  {rec.sample_id} -> {dest.name}")
        if args.dry_run:
            continue
        if dest.exists():
            print("    (exists, skip)")
            continue
        try:
            download_image(rec.image_path, dest)
            print("    ok")
        except Exception as exc:  # noqa: BLE001 — CLI tool surfaces network errors
            print(f"    failed: {exc}")


if __name__ == "__main__":
    main()
