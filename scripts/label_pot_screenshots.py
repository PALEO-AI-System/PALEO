"""
Simple interactive labeler for Path of Titans screenshots.

Binary labels:
  - predator
  - non_predator

Controls (matplotlib window focused):
  - p: predator
  - n: non_predator
  - s / right arrow: skip (leave blank)
  - backspace / left arrow: go back one image
  - q / esc: quit (progress is saved continuously)
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Row:
    filename: str
    label: str


def _read_labels_csv(path: Path) -> List[Row]:
    rows: List[Row] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = [fn.lstrip("\ufeff") for fn in (reader.fieldnames or [])]
        if not fieldnames or "filename" not in fieldnames or "label" not in fieldnames:
            raise ValueError("labels.csv must have headers: filename,label")
        for r in reader:
            # Some Windows tools write a UTF-8 BOM into the first header.
            filename = (r.get("filename") or r.get("\ufefffilename") or "").strip()
            label = (r.get("label") or "").strip()
            rows.append(Row(filename=filename, label=label))
    return rows


def _write_labels_csv(path: Path, rows: List[Row]) -> None:
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["filename", "label"])
        for r in rows:
            w.writerow([r.filename, r.label])
    tmp.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--images-dir",
        type=str,
        default="data/processed/pot_screenshots_300/images",
        help="Directory containing images to label.",
    )
    parser.add_argument(
        "--labels-csv",
        type=str,
        default="data/processed/pot_screenshots_300/labels.csv",
        help="CSV with columns filename,label.",
    )
    args = parser.parse_args()

    images_dir = Path(args.images_dir)
    labels_csv = Path(args.labels_csv)
    if not images_dir.exists():
        raise SystemExit(f"Missing images dir: {images_dir}")
    if not labels_csv.exists():
        raise SystemExit(f"Missing labels CSV: {labels_csv}")

    # Lazy imports so the file can be inspected without GUI deps.
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg

    rows = _read_labels_csv(labels_csv)
    by_name: Dict[str, int] = {r.filename: i for i, r in enumerate(rows) if r.filename}

    # Ensure CSV is in sync with the directory contents.
    image_files = sorted(
        [p for p in images_dir.iterdir() if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png")],
        key=lambda p: p.name.lower(),
    )
    for p in image_files:
        if p.name not in by_name:
            rows.append(Row(filename=p.name, label=""))
            by_name[p.name] = len(rows) - 1

    # Iterate in the same order as image_files.
    ordered_rows = [rows[by_name[p.name]] for p in image_files]

    def first_unlabeled_index() -> int:
        for i, r in enumerate(ordered_rows):
            if r.label.strip() == "":
                return i
        return 0

    idx = first_unlabeled_index()

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.canvas.manager.set_window_title("PALEO Labeler (p=predator, n=non_predator)")  # type: ignore[attr-defined]
    plt.tight_layout()

    status_text = ax.text(
        0.01,
        0.01,
        "",
        transform=ax.transAxes,
        fontsize=12,
        color="white",
        bbox=dict(boxstyle="round", facecolor="black", alpha=0.6),
    )

    def render() -> None:
        nonlocal idx
        if idx < 0:
            idx = 0
        if idx >= len(ordered_rows):
            idx = len(ordered_rows) - 1
        r = ordered_rows[idx]
        img_path = images_dir / r.filename
        ax.clear()
        img = mpimg.imread(str(img_path))
        ax.imshow(img)
        ax.axis("off")
        labeled = sum(1 for rr in ordered_rows if rr.label.strip())
        status_text = ax.text(
            0.01,
            0.01,
            f"{idx+1}/{len(ordered_rows)}  labeled={labeled}  file={r.filename}  label={r.label or '<blank>'}",
            transform=ax.transAxes,
            fontsize=12,
            color="white",
            bbox=dict(boxstyle="round", facecolor="black", alpha=0.6),
        )
        fig.canvas.draw_idle()

    def set_label(label: str) -> None:
        nonlocal idx
        ordered_rows[idx].label = label
        _write_labels_csv(labels_csv, ordered_rows)
        idx += 1
        if idx >= len(ordered_rows):
            idx = len(ordered_rows) - 1
        render()

    def skip() -> None:
        nonlocal idx
        idx += 1
        if idx >= len(ordered_rows):
            idx = len(ordered_rows) - 1
        render()

    def back() -> None:
        nonlocal idx
        idx -= 1
        if idx < 0:
            idx = 0
        render()

    def on_key(event) -> None:  # matplotlib event
        k = (event.key or "").lower()
        if k in ("p",):
            set_label("predator")
        elif k in ("n",):
            set_label("non_predator")
        elif k in ("s", "right"):
            skip()
        elif k in ("backspace", "left"):
            back()
        elif k in ("q", "escape"):
            plt.close(fig)

    fig.canvas.mpl_connect("key_press_event", on_key)
    render()
    plt.show()


if __name__ == "__main__":
    main()
