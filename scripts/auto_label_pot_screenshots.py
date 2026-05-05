"""
Auto-label Path of Titans screenshots using an existing ResNet-18 checkpoint.

This is intended for *pseudo-labeling* to speed up manual labeling:
- Writes per-image predicted label + confidence to auto_labels.csv
- Optionally fills blank labels in labels.csv (keeps any existing human labels)

Binary labels:
  predator -> class 1
  non_predator -> class 0
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image

from src.image_training import load_classifier, torch, transforms


@dataclass
class Pred:
    filename: str
    label: str
    confidence: float
    prob_predator: float
    prob_non_predator: float


def iter_images(images_dir: Path) -> List[Path]:
    return sorted(
        [
            p
            for p in images_dir.iterdir()
            if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
        ],
        key=lambda p: p.name.lower(),
    )


def read_labels_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = [fn.lstrip("\ufeff") for fn in (reader.fieldnames or [])]
        rows = []
        for r in reader:
            # Handle BOM on filename header if present.
            fn = (r.get("filename") or r.get("\ufefffilename") or "").strip()
            lab = (r.get("label") or "").strip()
            rows.append({"filename": fn, "label": lab})
        return rows, fieldnames


def write_labels_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["filename", "label"])
        for r in rows:
            w.writerow([r.get("filename", ""), r.get("label", "")])
    tmp.replace(path)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images-dir", type=str, default="data/processed/pot_screenshots_300/images")
    ap.add_argument("--labels-csv", type=str, default="data/processed/pot_screenshots_300/labels.csv")
    ap.add_argument(
        "--checkpoint",
        type=str,
        default="results/experiments/resnet18_lrie4_aug_e15/resnet18_serengeti_disk.pt",
    )
    ap.add_argument(
        "--out-csv",
        type=str,
        default="data/processed/pot_screenshots_300/auto_labels.csv",
        help="Where to write predictions (filename,label,confidence,prob_predator,prob_non_predator).",
    )
    ap.add_argument(
        "--fill-blanks",
        action="store_true",
        help="If set, fill blank entries in labels.csv with the model's predicted label.",
    )
    ap.add_argument(
        "--min-confidence",
        type=float,
        default=0.0,
        help="If --fill-blanks is set, only fill when confidence >= this threshold.",
    )
    ap.add_argument(
        "--pred-threshold",
        type=float,
        default=0.5,
        help="Predict predator when prob_predator >= this threshold (default: 0.5).",
    )
    ap.add_argument(
        "--eval-labels-csv",
        type=str,
        default="",
        help="Optional CSV (filename,label) to compute metrics and threshold sweep.",
    )
    ap.add_argument(
        "--eval-json",
        type=str,
        default="",
        help="Optional output JSON path for evaluation metrics.",
    )
    ap.add_argument(
        "--threshold-grid",
        type=str,
        default="0.3,0.35,0.4,0.45,0.5",
        help="Comma-separated predator thresholds to evaluate when --eval-labels-csv is provided.",
    )
    args = ap.parse_args()

    pred_threshold = float(args.pred_threshold)
    if not (0.0 <= pred_threshold <= 1.0):
        raise SystemExit("--pred-threshold must be in [0, 1].")

    images_dir = Path(args.images_dir)
    labels_csv = Path(args.labels_csv)
    ckpt = Path(args.checkpoint)
    out_csv = Path(args.out_csv)

    if torch is None or transforms is None:
        raise SystemExit("torch/torchvision unavailable; cannot auto-label.")
    if not images_dir.exists():
        raise SystemExit(f"Missing images dir: {images_dir}")
    if not ckpt.exists():
        raise SystemExit(f"Missing checkpoint: {ckpt}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = load_classifier(ckpt)
    model.to(device)
    model.eval()

    tfm = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    preds: List[Pred] = []
    for p in iter_images(images_dir):
        img = Image.open(p).convert("RGB")
        x = tfm(img).unsqueeze(0).to(device)
        with torch.no_grad():
            logits = model(x)
            probs = torch.softmax(logits, dim=1)[0].detach().cpu().tolist()
        non_pred, pred = float(probs[0]), float(probs[1])
        label = "predator" if pred >= pred_threshold else "non_predator"
        conf = max(pred, non_pred)
        preds.append(
            Pred(
                filename=p.name,
                label=label,
                confidence=float(conf),
                prob_predator=float(pred),
                prob_non_predator=float(non_pred),
            )
        )

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["filename", "label", "confidence", "prob_predator", "prob_non_predator"])
        for pr in preds:
            w.writerow(
                [
                    pr.filename,
                    pr.label,
                    f"{pr.confidence:.6f}",
                    f"{pr.prob_predator:.6f}",
                    f"{pr.prob_non_predator:.6f}",
                ]
            )

    if args.fill_blanks:
        if not labels_csv.exists():
            raise SystemExit(f"Missing labels CSV: {labels_csv}")
        rows, _ = read_labels_csv(labels_csv)
        pred_map = {p.filename: p for p in preds}
        filled = 0
        for r in rows:
            fn = (r.get("filename") or "").strip()
            lab = (r.get("label") or "").strip()
            if not fn or lab:
                continue
            pr = pred_map.get(fn)
            if pr is None:
                continue
            if pr.confidence >= float(args.min_confidence):
                r["label"] = pr.label
                filled += 1
        write_labels_csv(labels_csv, rows)
        print(f"Filled {filled} blank labels in {labels_csv}")

    if args.eval_labels_csv:
        eval_labels_csv = Path(args.eval_labels_csv)
        if not eval_labels_csv.exists():
            raise SystemExit(f"Missing eval labels CSV: {eval_labels_csv}")
        gt_rows, _ = read_labels_csv(eval_labels_csv)
        gt = {r["filename"]: r["label"] for r in gt_rows if r.get("filename") and r.get("label")}
        rows_by_name = {p.filename: p for p in preds}

        def _stats_for_threshold(thr: float) -> Dict[str, float | int | List[List[int]]]:
            tp = tn = fp = fn = 0
            total = 0
            for fnm, true_lab in gt.items():
                pr = rows_by_name.get(fnm)
                if pr is None:
                    continue
                total += 1
                pred_lab = "predator" if pr.prob_predator >= thr else "non_predator"
                if true_lab == "predator" and pred_lab == "predator":
                    tp += 1
                elif true_lab == "predator" and pred_lab == "non_predator":
                    fn += 1
                elif true_lab == "non_predator" and pred_lab == "predator":
                    fp += 1
                else:
                    tn += 1
            precision = tp / (tp + fp) if (tp + fp) else 0.0
            recall = tp / (tp + fn) if (tp + fn) else 0.0
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
            acc = (tp + tn) / total if total else 0.0
            return {
                "threshold": round(thr, 4),
                "num_scored": total,
                "accuracy": round(acc, 6),
                "predator_precision": round(precision, 6),
                "predator_recall": round(recall, 6),
                "predator_f1": round(f1, 6),
                "confusion_matrix_labels": ["non_predator", "predator"],
                "confusion_matrix": [[tn, fp], [fn, tp]],
            }

        thresholds: List[float] = []
        for raw in args.threshold_grid.split(","):
            s = raw.strip()
            if not s:
                continue
            v = float(s)
            if 0.0 <= v <= 1.0:
                thresholds.append(v)
        if pred_threshold not in thresholds:
            thresholds.append(pred_threshold)
        thresholds = sorted(set(thresholds))

        sweep = [_stats_for_threshold(t) for t in thresholds]
        current = _stats_for_threshold(pred_threshold)
        print(
            "eval "
            f"threshold={pred_threshold:.3f} "
            f"accuracy={current['accuracy']:.4f} "
            f"predator_recall={current['predator_recall']:.4f} "
            f"predator_precision={current['predator_precision']:.4f}"
        )

        if args.eval_json:
            eval_path = Path(args.eval_json)
            eval_path.parent.mkdir(parents=True, exist_ok=True)
            eval_path.write_text(
                json.dumps(
                    {
                        "labels_csv": str(eval_labels_csv),
                        "pred_threshold": pred_threshold,
                        "current_threshold_metrics": current,
                        "threshold_sweep": sweep,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            print(f"Wrote eval metrics: {eval_path}")

    print(f"Wrote predictions: {out_csv}")


if __name__ == "__main__":
    main()
