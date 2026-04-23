"""Generate report figures from saved experiment histories."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio

RESULTS_ROOT = PROJECT_ROOT / "results" / "experiments"
OUTPUT_DIR = PROJECT_ROOT / "output" / "figures"


def save_meta(path: Path, caption: str, description: str) -> None:
    import json
    path.with_suffix(path.suffix + ".meta.json").write_text(
        json.dumps({"caption": caption, "description": description}), encoding="utf-8"
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    histories = json.loads((RESULTS_ROOT / "all_histories.json").read_text(encoding="utf-8"))
    comparison = json.loads((RESULTS_ROOT / "comparison_table.json").read_text(encoding="utf-8"))

    # Only runs that actually trained (skip heuristic baseline + errored runs)
    model_runs = [
        r for r in histories
        if r.get("epochs", 0) > 0 and r.get("train_loss") and not r.get("error")
    ]

    # ── Figure 1: Convergence curves (train loss vs val loss)! ──────────────
    fig1 = go.Figure()
    for r in model_runs:
        epochs = list(range(1, len(r["train_loss"]) + 1))
        fig1.add_trace(go.Scatter(
            x=epochs, y=r["train_loss"], mode="lines+markers",
            name=f"{r['name']} train", line=dict(dash="solid")
        ))
        fig1.add_trace(go.Scatter(
            x=epochs, y=r["val_loss"], mode="lines+markers",
            name=f"{r['name']} val", line=dict(dash="dot")
        ))
    fig1.update_layout(
    title={
        "text": "Train vs Val Loss by Epoch<br><span style='font-size:16px;font-weight:normal'>Solid=train · Dotted=val · lower is better</span>",
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

    # ── Figure 2: Learning-rate sensitivity! ────────────────────────────────
    lr_rows = sorted(
    [r for r in comparison if r.get("learning_rate") is not None and r.get("augmentation") is True],
    key=lambda x: x["learning_rate"]
    )
    fig2 = go.Figure(go.Scatter(
        x=[str(r["learning_rate"]) for r in lr_rows],
        y=[r["final_val_acc"] for r in lr_rows],
        mode="lines+markers",
        fill="tozeroy"
    ))
    fig2.update_layout(
        title={"text": "Val Accuracy vs Learning Rate<br><span style='font-size:16px;font-weight:normal'>Higher = better · all runs 10 epochs</span>"}
    )
    fig2.update_xaxes(title_text="Learn rate")
    fig2.update_yaxes(title_text="Val acc", range=[0.9, 1.01])
    out2 = OUTPUT_DIR / "lr_sensitivity.png"
    fig2.write_image(str(out2))
    save_meta(out2, "Learning-rate sensitivity", "Final validation accuracy across learning rate values.")
    print(f"Saved {out2}")

    # ── Figure 3: Final val accuracy comparison bar chart! ──────────────────
    fig3 = px.bar(
        x=[r["experiment"] for r in comparison],
        y=[r["final_val_acc"] for r in comparison],
        text=[f"{r['final_val_acc']:.3f}" for r in comparison]
    )
    fig3.update_traces(textposition="outside", cliponaxis=False)
    fig3.update_layout(
        title={"text": "Final Val Accuracy by Experiment<br><span style='font-size:16px;font-weight:normal'>Baseline vs ResNet-18 variants</span>"}
    )
    fig3.update_xaxes(title_text="Experiment", tickangle=-30)
    fig3.update_yaxes(title_text="Val acc", range=[0.9, 1.05])
    out3 = OUTPUT_DIR / "final_comparison.png"
    fig3.write_image(str(out3))
    save_meta(out3, "Final val accuracy comparison", "Bar chart comparing heuristic baseline and all ResNet-18 training configurations.")
    print(f"Saved {out3}")


if __name__ == "__main__":
    main()