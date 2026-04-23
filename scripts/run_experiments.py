# Purpose: run a sweep of resnet-18 training experiments + save comparison table

from __future__ import annotations
import json
import sys
from pathlib import Path

daProjectRoot = Path(__file__).resolve().parents[1]
if str(daProjectRoot) not in sys.path:
    sys.path.insert(0, str(daProjectRoot))

from src.config import default_data_config
from src.data   import ensure_data_dirs, load_manifest
from src.image_training import train_serengeti_predator_on_disk
from src.training import TrainingConfig

EXPERIMENTS = [
{"name": "heuristic_baseline", "lr": None, "epochs":0, "augment":False},
{"name": "resnet18_lrie3_noaug", "lr": 1e-3, "epochs": 10, "augment": False},
{"name": "resnet18_lrie3_aug",   "lr": 1e-3, "epochs": 10, "augment": True},
{"name": "resnet18_lrie4_noaug", "lr": 1e-4, "epochs": 10, "augment": True},
{"name": "resnet18_lr5e5_aug", "lr": 5e-5, "epochs": 10, "augment": True},
]

daRESULTSROOT = daProjectRoot / "results" / "experiments"

def heuristic_baselineMetrics() -> dict:
    data_cfg=default_data_config()
    records = load_manifest(data_cfg)
    val = [r for r in records if r.split == "val"]
    if not val:
        return {"val_acc": 0.0, "note": "no_val_records"}
    majority_acc=sum(1 for r in val if r.predator_label==0)/len(val)
    return {"val_acc": majority_acc, "note": "majority_class_heuristic"}

def run_experiments(exp: dict, images_root:Path)->dict:
    out_dir = daRESULTSROOT / exp["name"]
    data_cfg=default_data_config()
    records=load_manifest(data_cfg)

    tcfg=TrainingConfig(
        epochs=exp["epochs"],
        learning_rate=exp["lr"],
        batch_size=16,
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
    data_cfg=default_data_config()
    ensure_data_dirs(data_cfg)
    images_root = data_cfg.processed_dir/"serengeti_images"
    daRESULTSROOT.mkdir(parents=True, exist_ok=True)
    all_results = []
    for exp in EXPERIMENTS:
        print(f"\n{'='*50}")
        print(f"Running experiment: {exp['name']}")
        print(f"{'='*50}\n")

        if exp["lr"] is None:
            metrics = heuristic_baselineMetrics()
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
                result=run_experiments(exp, images_root)
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
    

