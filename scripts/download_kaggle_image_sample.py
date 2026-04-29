"""Download or extract a capped image sample from a Kaggle dataset.

Examples:
  python scripts/download_kaggle_image_sample.py --dataset sttaseen/animal-behaviour --max-images 1000 --include-video-frames
  python scripts/download_kaggle_image_sample.py --dataset owner/dataset --max-images 1000
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path
from zipfile import ZipFile


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv"}


def _run_kaggle(args: list[str]) -> str:
    scripts_dir = Path(sysconfig.get_path("scripts"))
    kaggle_exe = shutil.which("kaggle") or str(scripts_dir / "kaggle.exe")
    cmd = [kaggle_exe, *args]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(
            "Kaggle command failed:\n"
            f"  {' '.join(cmd)}\n"
            f"{detail}"
        )
    return proc.stdout


def _dataset_slug_name(dataset: str) -> str:
    return dataset.replace("/", "__").replace(" ", "_")


def list_dataset_files(dataset: str) -> list[str]:
    """Return Kaggle dataset file names from `kaggle datasets files` output."""
    out = _run_kaggle(["datasets", "files", "-d", dataset])
    files: list[str] = []
    for raw in out.splitlines():
        line = raw.strip()
        if not line or line.startswith("name ") or line.startswith("---"):
            continue
        first = line.split()[0]
        if "." in first:
            files.append(first)
    return files


def download_dataset_file(dataset: str, file_name: str, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    downloaded = dest_dir / Path(file_name).name
    if downloaded.exists():
        return downloaded
    _run_kaggle(
        [
            "datasets",
            "download",
            "-d",
            dataset,
            "-f",
            file_name,
            "-p",
            str(dest_dir),
            "--force",
        ]
    )
    zip_path = downloaded.with_suffix(downloaded.suffix + ".zip")
    if zip_path.exists():
        with ZipFile(zip_path) as zf:
            zf.extractall(dest_dir)
    return downloaded


def extract_video_frames(video_path: Path, out_dir: Path, remaining: int, every_n: int) -> int:
    import cv2

    out_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"Could not open video: {video_path}")
        return 0

    written = 0
    frame_idx = 0
    stem = video_path.stem.replace(" ", "_")
    while written < remaining:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_idx % every_n == 0:
            out_path = out_dir / f"{stem}_frame_{frame_idx:08d}.jpg"
            cv2.imwrite(str(out_path), frame)
            written += 1
        frame_idx += 1
    cap.release()
    return written


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a capped local image sample from a Kaggle dataset."
    )
    parser.add_argument("--dataset", required=True, help="Kaggle slug, e.g. sttaseen/animal-behaviour.")
    parser.add_argument("--max-images", type=int, default=1000, help="Maximum images/frames to create.")
    parser.add_argument(
        "--out-dir",
        default="",
        help="Output directory for image sample. Default: data/processed/kaggle_image_samples/<dataset>.",
    )
    parser.add_argument(
        "--download-dir",
        default="",
        help="Temporary Kaggle download directory. Default: data/raw/kaggle/_sample_downloads/<dataset>.",
    )
    parser.add_argument(
        "--include-video-frames",
        action="store_true",
        help="If the dataset has videos, download videos and extract JPEG frames.",
    )
    parser.add_argument(
        "--frame-step",
        type=int,
        default=30,
        help="Extract one frame every N video frames.",
    )
    parser.add_argument("--list-only", action="store_true", help="Only list candidate files.")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    slug = _dataset_slug_name(args.dataset)
    out_dir = Path(args.out_dir) if args.out_dir else project_root / "data" / "processed" / "kaggle_image_samples" / slug
    download_dir = (
        Path(args.download_dir)
        if args.download_dir
        else project_root / "data" / "raw" / "kaggle" / "_sample_downloads" / slug
    )

    files = list_dataset_files(args.dataset)
    image_files = [f for f in files if Path(f).suffix.lower() in IMAGE_EXTS]
    video_files = [f for f in files if Path(f).suffix.lower() in VIDEO_EXTS]

    print(f"Dataset: {args.dataset}")
    print(f"Image files: {len(image_files)}")
    print(f"Video files: {len(video_files)}")
    if args.list_only:
        for f in image_files[:20]:
            print(f"image: {f}")
        for f in video_files[:20]:
            print(f"video: {f}")
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    created = 0

    for file_name in image_files:
        if created >= args.max_images:
            break
        downloaded = download_dataset_file(args.dataset, file_name, download_dir)
        candidates = [downloaded]
        if not downloaded.exists():
            candidates = list(download_dir.rglob(Path(file_name).name))
        for candidate in candidates:
            if candidate.exists() and candidate.suffix.lower() in IMAGE_EXTS:
                target = out_dir / f"{created:05d}_{candidate.name}"
                target.write_bytes(candidate.read_bytes())
                created += 1
                print(f"image {created}/{args.max_images}: {target}")
                break

    if args.include_video_frames and created < args.max_images:
        for file_name in video_files:
            if created >= args.max_images:
                break
            downloaded = download_dataset_file(args.dataset, file_name, download_dir)
            videos = [downloaded] if downloaded.exists() else list(download_dir.rglob(Path(file_name).name))
            for video in videos:
                if created >= args.max_images:
                    break
                if video.suffix.lower() not in VIDEO_EXTS:
                    continue
                made = extract_video_frames(
                    video,
                    out_dir,
                    remaining=args.max_images - created,
                    every_n=max(args.frame_step, 1),
                )
                created += made
                print(f"frames from {video.name}: +{made}, total {created}/{args.max_images}")

    print(f"Done. Created {created} images in {out_dir}")
    if created == 0 and video_files and not args.include_video_frames:
        print("This dataset appears to contain videos. Re-run with --include-video-frames.")


if __name__ == "__main__":
    main()
