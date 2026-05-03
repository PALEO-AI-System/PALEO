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
from src.image_training import (
    train_serengeti_predator_on_disk,
    load_classifier,
    _split_train_val,
    SerengetiDiskDataset,
    is_torch_available,
)
from src.serengeti_image_paths import list_records_with_local_files
from src.training import TrainingConfig

EXPERIMENTS = [
    {"name": "heuristic_baseline", "lr": None, "epochs": 0, "augment": False},
    {"name": "resnet18_lrie3_noaug_e10", "lr": 1e-3, "epochs": 10, "augment": False},
    {"name": "resnet18_lrie3_noaug_e5", "lr": 1e-3, "epochs": 5, "augment": False},
    {"name": "resnet18_lrie3_aug_e10", "lr": 1e-3, "epochs": 10, "augment": True},
    {"name": "resnet18_lrie4_aug_e10", "lr": 1e-4, "epochs": 10, "augment": True},
    {"name": "resnet18_lr5e5_aug_e10", "lr": 5e-5, "epochs": 10, "augment": True},
    {"name": "resnet18_lrie3_noaug_e15", "lr": 1e-3, "epochs": 15, "augment": False},
    {"name": "resnet18_lrie3_aug_e15", "lr": 1e-3, "epochs": 15, "augment": True},
    {"name": "resnet18_lrie4_aug_e15", "lr": 1e-4, "epochs": 15, "augment": True},
    {"name": "resnet18_lr5e5_aug_e15", "lr": 5e-5, "epochs": 15, "augment": True},
]

daRESULTSROOT = daProjectRoot / "results" / "experiments"

def _balanced_records(records: list, max_per_class: int) -> list:
    if max_per_class <= 0:
        return records
    predators = [r for r in records if r.predator_label == 1][:max_per_class]
    non_predators = [r for r in records if r.predator_label == 0][:max_per_class]
    balanced = []
    for pred, non_pred in zip(predators, non_predators):
        balanced.extend([pred, non_pred])
    return balanced


def _evaluate_failure_analysis(
    records: list,
    images_root: Path,
    out_dir: Path,
    split_seed: int,
    val_fraction: float = 0.2,
) -> dict:
    try:
        import torch
    except ImportError:
        return {"note": "torch_unavailable", "num_val": 0}

    model_path = out_dir / "resnet18_serengeti_disk.pt"
    if not model_path.exists():
        return {"note": "checkpoint_missing", "path": str(model_path)}

    local_records = list_records_with_local_files(records, images_root)
    _, val_recs = _split_train_val(local_records, val_fraction=val_fraction, seed=split_seed)
    if not val_recs:
        return {"note": "no_val_records", "num_val": 0}

    try:
        model = load_classifier(model_path)
    except Exception as exc:
        return {"note": "classifier_load_failed", "error": str(exc)}

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()

    val_ds = SerengetiDiskDataset(val_recs, images_root, augment=False)
    confusion = {"tp": 0, "tn": 0, "fp": 0, "fn": 0}
    failures = []

    with torch.no_grad():
        for rec_idx in range(len(val_ds)):
            xb, yb = val_ds[rec_idx]
            xb = xb.unsqueeze(0).to(device)
            yb = yb.to(device)
            logits = model(xb)
            pred = int(logits.argmax(dim=1).item())
            actual = int(yb.item())
            correct = pred == actual
            if actual == 1 and pred == 1:
                confusion["tp"] += 1
            elif actual == 0 and pred == 0:
                confusion["tn"] += 1
            elif actual == 0 and pred == 1:
                confusion["fp"] += 1
            else:
                confusion["fn"] += 1
            if not correct:
                failures.append(
                    {
                        "sample_id": val_recs[rec_idx].sample_id,
                        "image_path": val_recs[rec_idx].image_path,
                        "predator_label": actual,
                        "predicted_label": pred,
                        "split": val_recs[rec_idx].split,
                    }
                )

    summary = {
        "num_val": len(val_recs),
        "num_failures": len(failures),
        "confusion": confusion,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    failure_path = out_dir / "failure_analysis.json"
    failure_path.write_text(json.dumps({"summary": summary, "failures": failures}, indent=2), encoding="utf-8")
    return summary


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
    data_cfg = default_data_config()

    print(f"Starting experiment {exp['name']} with {len(records)} records, lr={exp['lr']}, epochs={exp['epochs']}, augment={exp['augment']}")
    sys.stdout.flush()

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
    parser.add_argument(
        "--balanced",
        action="store_true",
        help="Enforce balanced predator/non-predator sampling when capping records.",
    )
    parser.add_argument("--batch-size", type=int, default=16, help="Training batch size.")
    parser.add_argument(
        "--failure-analysis",
        action="store_true",
        help="Run post-training failure analysis on the validation set.",
    )
    args = parser.parse_args()

    data_cfg = default_data_config()
    ensure_data_dirs(data_cfg)
    torch_ready = is_torch_available()
    if not torch_ready:
        print("WARNING: torch and torchvision are not installed.")
        print("ResNet experiments will be skipped; only heuristic_baseline can run.")
        print("Install with: python -m pip install torch torchvision")
    images_root = Path(args.images_root) if args.images_root else data_cfg.processed_dir/"serengeti_images"
    raw_records = list_records_with_local_files(load_manifest(data_cfg), images_root)
    total_pred = sum(1 for r in raw_records if r.predator_label == 1)
    total_non = sum(1 for r in raw_records if r.predator_label == 0)
    print(f"Found {len(raw_records)} local records: {total_pred} predators, {total_non} non-predators.")
    records = raw_records
    if args.max_local_per_class > 0:
        if args.balanced:
            print(f"Balancing dataset with up to {args.max_local_per_class} samples per class.")
        records = _balanced_records(records, args.max_local_per_class)
    capped_pred = sum(1 for r in records if r.predator_label == 1)
    capped_non = sum(1 for r in records if r.predator_label == 0)
    print(f"Using {len(records)} records after cap: {capped_pred} predators, {capped_non} non-predators.")
    if args.epochs > 0:
        for exp in EXPERIMENTS:
            if exp["epochs"] > 0:
                exp["epochs"] = args.epochs
    daRESULTSROOT.mkdir(parents=True, exist_ok=True)
    all_results = []
    for exp_idx, exp in enumerate(EXPERIMENTS, start=1):
        print(f"\n{'='*50}")
        print(f"Experiment {exp_idx}/{len(EXPERIMENTS)}: {exp['name']}")
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
            if not torch_ready:
                print(
                    f" Skipped - ResNet experiment {exp['name']} cannot run because torch is unavailable."
                )
                result = {
                    "name": exp["name"],
                    "lr": exp.get("lr"),
                    "augment": exp.get("augment"),
                    "epochs": exp.get("epochs"),
                    "error": "torch_unavailable",
                    "final_val_acc": None,
                }
            else:
                try:
                    result = run_experiments(exp, images_root, records, args.batch_size)
                    print(f"Final val_acc:{result['final_val_acc']:.4f}")
                    if args.failure_analysis:
                        analysis = _evaluate_failure_analysis(
                            records,
                            images_root,
                            daRESULTSROOT / exp["name"],
                            split_seed=data_cfg.split_seed,
                            val_fraction=0.2,
                        )
                        result["failure_analysis"] = analysis
                        if analysis.get("num_val"):
                            print(
                                f"Saved failure analysis for {exp['name']} with {analysis.get('num_failures', 0)} failures."
                            )
                        else:
                            print(f"Failure analysis skipped: {analysis.get('note')}")
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
    

