"""Generate report figures from saved experiment histories."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import plotly.express as px
import plotly.graph_objects as go

RESULTS_ROOT = PROJECT_ROOT / "results" / "experiments"
OUTPUT_DIR = PROJECT_ROOT / "output" / "figures"


def save_meta(path: Path, caption: str, description: str) -> None:
    path.with_suffix(path.suffix + ".meta.json").write_text(
        json.dumps({"caption": caption, "description": description}), encoding="utf-8"
    )


def accuracy_axis_range(values: list[float]) -> list[float]:
    clean = [float(v) for v in values if v is not None]
    if not clean:
        return [0, 1]
    low = max(0, min(clean) - 0.05)
    high = min(1.05, max(clean) + 0.05)
    if high - low < 0.1:
        low = max(0, low - 0.05)
        high = min(1.05, high + 0.05)
    return [low, high]


def _build_run_from_metrics(exp_dir: Path, metrics: dict) -> dict:
    if exp_dir.name == "heuristic_baseline":
        return {
            "name": exp_dir.name,
            "lr": None,
            "augment": False,
            "epochs": 0,
            "final_val_acc": metrics.get("val_acc"),
            "train_loss": [],
            "val_loss": [],
            "train_acc": [],
        }

    lr_list = metrics.get("learning_rate", [])
    lr_value = lr_list[0] if isinstance(lr_list, list) and lr_list else None
    epochs = len(metrics.get("epochs", []))
    augment = "_aug" in exp_dir.name and "_noaug" not in exp_dir.name
    val_acc = metrics.get("val_acc", [])
    final_val_acc = val_acc[-1] if isinstance(val_acc, list) and val_acc else None

    return {
        "name": exp_dir.name,
        "lr": lr_value,
        "augment": augment,
        "epochs": epochs,
        "final_val_acc": final_val_acc,
        "train_loss": metrics.get("train_loss", []),
        "val_loss": metrics.get("val_loss", []),
        "train_acc": metrics.get("train_acc", []),
    }


def load_experiment_data() -> tuple[list[dict], list[dict]]:
    """Load experiments from per-run metrics and dedupe by settings.

    If legacy and renamed folders exist for the same setting, keep the newest metrics file.
    """
    keyed_runs: dict[tuple[float | None, bool, int], dict] = {}
    keyed_mtime: dict[tuple[float | None, bool, int], float] = {}

    for exp_dir in RESULTS_ROOT.iterdir():
        if not exp_dir.is_dir():
            continue
        metrics_path = exp_dir / "metrics.json"
        if not metrics_path.exists():
            continue

        try:
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        run = _build_run_from_metrics(exp_dir, metrics)
        key = (run["lr"], run["augment"], run["epochs"])
        mtime = metrics_path.stat().st_mtime

        if key not in keyed_runs or mtime > keyed_mtime[key]:
            keyed_runs[key] = run
            keyed_mtime[key] = mtime

    histories = sorted(keyed_runs.values(), key=lambda r: (r["epochs"], str(r["name"])))
    comparison = [
        {
            "experiment": r["name"],
            "learning_rate": r["lr"],
            "augmentation": r["augment"],
            "epochs": r["epochs"],
            "final_val_acc": r["final_val_acc"],
        }
        for r in histories
    ]
    return histories, comparison


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    histories, comparison = load_experiment_data()

    model_runs = [
        r for r in histories if r.get("epochs", 0) > 0 and r.get("train_loss") and r.get("final_val_acc") is not None
    ]

    fig1 = go.Figure()
    for r in model_runs:
        epochs = list(range(1, len(r["train_loss"]) + 1))
        fig1.add_trace(
            go.Scatter(
                x=epochs,
                y=r["train_loss"],
                mode="lines+markers",
                name=f"{r['name']} train",
                line=dict(dash="solid"),
            )
        )
        fig1.add_trace(
            go.Scatter(
                x=epochs,
                y=r["val_loss"],
                mode="lines+markers",
                name=f"{r['name']} val",
                line=dict(dash="dot"),
            )
        )
    fig1.update_layout(
        title={
            "text": "Train vs Val Loss by Epoch<br><span style='font-size:16px;font-weight:normal'>Solid=train - Dotted=val - lower is better</span>",
            "y": 0.97,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font=dict(size=10),
        ),
        margin=dict(t=80, b=180),
    )
    fig1.update_xaxes(title_text="Epoch")
    fig1.update_yaxes(title_text="Loss")
    out1 = OUTPUT_DIR / "convergence_curves.png"
    fig1.write_image(str(out1))
    save_meta(out1, "Convergence curves", "Train and val loss per epoch for each ResNet-18 experiment run.")
    print(f"Saved {out1}")

    lr_rows = sorted(
        [r for r in comparison if r.get("learning_rate") is not None and r.get("augmentation") is True],
        key=lambda x: (x["epochs"], x["learning_rate"]),
    )
    lr_values = [r["final_val_acc"] for r in lr_rows if r.get("final_val_acc") is not None]
    fig2 = go.Figure(
        go.Scatter(
            x=[f"e{r['epochs']} | lr={r['learning_rate']}" for r in lr_rows],
            y=[r["final_val_acc"] for r in lr_rows],
            mode="lines+markers",
            fill="tozeroy",
        )
    )
    fig2.update_layout(
        title={
            "text": "Val Accuracy vs Learning Rate<br><span style='font-size:16px;font-weight:normal'>Higher = better - augmented runs across available epochs</span>"
        }
    )
    fig2.update_xaxes(title_text="Epoch + Learning rate", tickangle=-25)
    fig2.update_yaxes(title_text="Val acc", range=accuracy_axis_range(lr_values))
    out2 = OUTPUT_DIR / "lr_sensitivity.png"
    fig2.write_image(str(out2))
    save_meta(out2, "Learning-rate sensitivity", "Final validation accuracy across learning-rate settings for augmented runs.")
    print(f"Saved {out2}")

    bar_rows = [r for r in comparison if r.get("final_val_acc") is not None]
    bar_values = [r["final_val_acc"] for r in bar_rows]
    fig3 = px.bar(
        x=[r["experiment"] for r in bar_rows],
        y=[r["final_val_acc"] for r in bar_rows],
        text=[f"{r['final_val_acc']:.3f}" for r in bar_rows],
    )
    fig3.update_traces(textposition="outside", cliponaxis=False)
    fig3.update_layout(
        title={
            "text": "Final Val Accuracy by Experiment<br><span style='font-size:16px;font-weight:normal'>Baseline plus all available ResNet-18 runs</span>"
        }
    )
    fig3.update_xaxes(title_text="Experiment", tickangle=-30)
    fig3.update_yaxes(title_text="Val acc", range=accuracy_axis_range(bar_values))
    out3 = OUTPUT_DIR / "final_comparison.png"
    fig3.write_image(str(out3))
    save_meta(out3, "Final val accuracy comparison", "Bar chart comparing heuristic baseline and all available ResNet-18 configurations.")
    print(f"Saved {out3}")


if __name__ == "__main__":
    main()
