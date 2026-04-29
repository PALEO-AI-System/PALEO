# Purpose: run a sweep of resnet-18 training experiments + save comparison table

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

daProjectRoot = Path(__file__).resolve().parents[1]
if str(daProjectRoot) not in sys.path:
    sys.path.insert(0, str(daProjectRoot))

from src.config import default_data_config
from src.data   import ensure_data_dirs, load_manifest
from src.image_training import train_serengeti_predator_on_disk
from src.serengeti_image_paths import list_records_with_local_files
from src.training import TrainingConfig

EXPERIMENTS = [
{"name": "heuristic_baseline", "lr": None, "epochs":0, "augment":False},
{"name": "resnet18_lrie3_noaug", "lr": 1e-3, "epochs": 10, "augment": False},
{"name": "resnet18_lrie3_aug",   "lr": 1e-3, "epochs": 10, "augment": True},
{"name": "resnet18_lrie4_noaug", "lr": 1e-4, "epochs": 10, "augment": True},
{"name": "resnet18_lr5e5_aug", "lr": 5e-5, "epochs": 10, "augment": True},
]

daRESULTSROOT = daProjectRoot / "results" / "experiments"

def _cap_records_per_class(records: list, max_per_class: int) -> list:
    if max_per_class <= 0:
        return records
    predators = [r for r in records if r.predator_label == 1][:max_per_class]
    non_predators = [r for r in records if r.predator_label == 0][:max_per_class]
    capped = []
    for pred, non_pred in zip(predators, non_predators):
        capped.extend([pred, non_pred])
    return capped


def heuristic_baselineMetrics(records: list) -> dict:
    val = [r for r in records if r.split == "val"]
    if not val:
        return {"val_acc": 0.0, "note": "no_val_records"}
    positives = sum(r.predator_label for r in val)
    negatives = len(val) - positives
    majority_acc=max(positives, negatives)/len(val)
    return {"val_acc": majority_acc, "note": "majority_class_heuristic"}

def run_experiments(exp: dict, images_root:Path, records: list, batch_size: int)->dict:
    out_dir = daRESULTSROOT / exp["name"]
    data_cfg=default_data_config()

    tcfg=TrainingConfig(
        epochs=exp["epochs"],
        learning_rate=exp["lr"],
        batch_size=batch_size,
        output_dir=str(out_dir),
        model_name=exp["name"],
    )
    history = train_serengeti_predator_on_disk(
        records,
        images_root,
        tcfg,
        val_fraction=0.2,
        split_seed=data_cfg.split_seed,
        augment=exp["augment"],
    )
    final_val_acc = history["val_acc"][-1] if history["val_acc"] else 0.0
    return{
        "name": exp["name"],
        "lr": exp["lr"],
        "augment": exp["augment"],
        "epochs": exp["epochs"],
        "final_val_acc": final_val_acc,
        "train_loss": history.get("train_loss",[]),
        "val_loss": history.get("val_loss",[]),
        "train_acc": history.get("train_acc",[]),
    }

def main()-> None:
    parser = argparse.ArgumentParser(description="Run PALEO baseline and ResNet-18 experiments.")
    parser.add_argument(
        "--images-root",
        type=str,
        default="",
        help="Override local image folder. Default: data/processed/serengeti_images.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=0,
        help="Override non-baseline experiment epochs. Useful for CPU smoke runs.",
    )
    parser.add_argument(
        "--max-local-per-class",
        type=int,
        default=0,
        help="Cap local records per class after filtering by --images-root.",
    )
    parser.add_argument("--batch-size", type=int, default=16, help="Training batch size.")
    args = parser.parse_args()

    data_cfg=default_data_config()
    ensure_data_dirs(data_cfg)
    images_root = Path(args.images_root) if args.images_root else data_cfg.processed_dir/"serengeti_images"
    records = list_records_with_local_files(load_manifest(data_cfg), images_root)
    records = _cap_records_per_class(records, args.max_local_per_class)
    if args.epochs > 0:
        for exp in EXPERIMENTS:
            if exp["epochs"] > 0:
                exp["epochs"] = args.epochs
    daRESULTSROOT.mkdir(parents=True, exist_ok=True)
    all_results = []
    for exp in EXPERIMENTS:
        print(f"\n{'='*50}")
        print(f"Running experiment: {exp['name']}")
        print(f"{'='*50}\n")

        if exp["lr"] is None:
            metrics = heuristic_baselineMetrics(records)
            result = {
                "name": exp["name"],
                "lr": None,
                "augment": False,
                "epochs": 0,
                "final_val_acc": metrics["val_acc"],
                "note": metrics.get("note", ""),
                "train_loss": [],
                "val_loss": [],
                "train_acc": [],
            }
            out_dir = daRESULTSROOT / exp["name"]
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=4))
            print(f"Saved heuristic baseline metrics to {out_dir / 'metrics.json'}")
        else:
            try:
                result=run_experiments(exp, images_root, records, args.batch_size)
                print(f"Final val_acc:{result['final_val_acc']:.4f}")
            except RuntimeError as e:
                print(f" Skipped - {e}")
                result={
                    "name": exp["name"],
                    "lr": exp.get("lr"),
                    "augment": exp.get("augment"),
                    "epochs": exp.get("epochs"),
                    "error": str(e),
                    "final_val_acc": None,
                }
        all_results.append(result)
    table_path = daRESULTSROOT / "comparison_table.json"
    table_rows = [
        {
            "experiment": r.get("name"),
            "learning_rate": r.get("lr"),
            "augmentation": r.get("augment"),
            "epochs": r.get("epochs"),
            "final_val_acc": r.get("final_val_acc"),
        }
        for r in all_results
    ]
    table_path.write_text(json.dumps(table_rows, indent=4))
    print(f"\nSaved comparison table to {table_path}")

    history_path = daRESULTSROOT / "all_histories.json"
    history_path.write_text(json.dumps(all_results, indent=4))
    print(f"Full histories saved to {history_path}")

if __name__ == "__main__":    main()
    

