"""Calibrate Path of Titans HUD parser on real screenshots.

This script:
- scans screenshots
- runs parse_pot_hud() on each frame
- draws ROI debug overlays
- writes summary JSON/CSV for threshold tuning
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pot import parse_pot_hud

try:
    import cv2
except Exception:  # pragma: no cover - optional runtime dep
    cv2 = None

try:
    import numpy as np
except Exception:  # pragma: no cover - optional runtime dep
    np = None


ROI_BOXES: Dict[str, Tuple[float, float, float, float]] = {
    "health": (0.17, 0.79, 0.84, 0.84),
    "stamina": (0.18, 0.845, 0.44, 0.89),
    "hunger_icon": (0.06, 0.76, 0.15, 0.93),
    "thirst_icon": (0.85, 0.76, 0.94, 0.93),
    "abilities_lane": (0.36, 0.69, 0.66, 0.79),
    "buffs_lane": (0.33, 0.61, 0.69, 0.69),
}


def _iter_images(images_dir: Path) -> List[Path]:
    out: List[Path] = []
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp"):
        out.extend(images_dir.rglob(ext))
    out = [p for p in out if p.is_file()]
    out.sort(key=lambda p: p.name.lower())
    return out


def _roi_px(box: Tuple[float, float, float, float], w: int, h: int) -> Tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    ix0 = max(0, min(w - 1, int(x0 * w)))
    iy0 = max(0, min(h - 1, int(y0 * h)))
    ix1 = max(ix0 + 1, min(w, int(x1 * w)))
    iy1 = max(iy0 + 1, min(h, int(y1 * h)))
    return ix0, iy0, ix1, iy1


def _draw_overlay(img_bgr, label_rows: List[str]):
    if cv2 is None:
        return img_bgr
    out = img_bgr.copy()
    h, w = out.shape[:2]
    colors = {
        "health": (0, 0, 255),
        "stamina": (240, 240, 240),
        "hunger_icon": (0, 255, 0),
        "thirst_icon": (255, 0, 0),
        "abilities_lane": (0, 180, 255),
        "buffs_lane": (160, 80, 220),
    }
    for name, box in ROI_BOXES.items():
        x0, y0, x1, y1 = _roi_px(box, w, h)
        c = colors.get(name, (180, 180, 180))
        cv2.rectangle(out, (x0, y0), (x1, y1), c, 2)
        cv2.putText(out, name, (x0 + 4, max(16, y0 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, c, 1, cv2.LINE_AA)

    y = 20
    for row in label_rows:
        cv2.putText(out, row, (14, y), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (220, 255, 220), 1, cv2.LINE_AA)
        y += 20
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Calibrate PoT HUD parser with debug overlays.")
    ap.add_argument("--images-dir", default="data/processed/pot_hud_calibration/images")
    ap.add_argument("--out-dir", default="results/hud_calibration")
    ap.add_argument("--limit", type=int, default=0, help="Optional max images; 0 means all.")
    args = ap.parse_args()

    if cv2 is None or np is None:
        raise SystemExit("opencv-python and numpy are required for HUD calibration.")

    images_dir = Path(args.images_dir)
    out_dir = Path(args.out_dir)
    overlay_dir = out_dir / "overlays"
    out_dir.mkdir(parents=True, exist_ok=True)
    overlay_dir.mkdir(parents=True, exist_ok=True)

    if not images_dir.exists():
        raise SystemExit(f"Missing images dir: {images_dir}")

    images = _iter_images(images_dir)
    if args.limit and args.limit > 0:
        images = images[: int(args.limit)]
    if not images:
        raise SystemExit(f"No images found in: {images_dir}")

    rows: List[Dict[str, object]] = []
    for i, p in enumerate(images, start=1):
        img = cv2.imread(str(p), cv2.IMREAD_COLOR)
        if img is None:
            continue
        hud = parse_pot_hud(img)
        if hud is None:
            continue
        row = {
            "filename": p.name,
            "health": hud.health,
            "stamina": hud.stamina,
            "hunger": hud.hunger,
            "thirst": hud.thirst,
            "stamina_hidden_full": bool(hud.stamina_hidden_full),
            "abilities_lane_visible": bool(hud.abilities_lane_visible),
            "buffs_lane_visible": bool(hud.buffs_lane_visible),
            "confidence": hud.confidence,
        }
        rows.append(row)

        label_rows = [
            f"file={p.name}",
            f"health={hud.health:.3f} stamina={hud.stamina:.3f} hidden_full={hud.stamina_hidden_full}",
            f"hunger={hud.hunger:.3f} thirst={hud.thirst:.3f} conf={hud.confidence:.3f}",
            f"abilities={hud.abilities_lane_visible} buffs={hud.buffs_lane_visible}",
        ]
        overlay = _draw_overlay(img, label_rows)
        out_path = overlay_dir / p.name
        cv2.imwrite(str(out_path), overlay)
        print(f"[{i}/{len(images)}] calibrated {p.name}")

    if not rows:
        raise SystemExit("No HUD rows produced; check screenshot content/UI visibility.")

    csv_path = out_dir / "hud_values.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "filename",
                "health",
                "stamina",
                "hunger",
                "thirst",
                "stamina_hidden_full",
                "abilities_lane_visible",
                "buffs_lane_visible",
                "confidence",
            ],
        )
        w.writeheader()
        w.writerows(rows)

    conf = [float(r["confidence"]) for r in rows]
    health = [float(r["health"]) for r in rows]
    stamina = [float(r["stamina"]) for r in rows]
    hunger = [float(r["hunger"]) for r in rows]
    thirst = [float(r["thirst"]) for r in rows]
    summary = {
        "num_images_scored": len(rows),
        "confidence_mean": round(sum(conf) / len(conf), 4),
        "health_mean": round(sum(health) / len(health), 4),
        "stamina_mean": round(sum(stamina) / len(stamina), 4),
        "hunger_mean": round(sum(hunger) / len(hunger), 4),
        "thirst_mean": round(sum(thirst) / len(thirst), 4),
        "suggested_min_confidence": round(max(0.45, (sum(conf) / len(conf)) * 0.7), 4),
        "paths": {
            "csv": str(csv_path).replace("\\", "/"),
            "overlay_dir": str(overlay_dir).replace("\\", "/"),
        },
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
