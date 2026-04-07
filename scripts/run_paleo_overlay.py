"""Transparent always-on-top PALEO overlay (screen sidecar)."""

from __future__ import annotations

import argparse
import json
import sys
import time
import tkinter as tk
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import default_pot_config
from src.letta_tools import simulate_instinct_decision
from src.pot import ActionMapper, SafeInputController, ScreenCaptureWorker, frame_to_observation


def main() -> None:
    p = argparse.ArgumentParser(description="PALEO transparent overlay HUD.")
    p.add_argument("--species", default="allosaurus")
    p.add_argument("--fps", type=float, default=4.0)
    p.add_argument("--mode", choices=["advice", "control"], default="advice")
    p.add_argument("--enable-control", action="store_true")
    p.add_argument("--x", type=int, default=24)
    p.add_argument("--y", type=int, default=24)
    args = p.parse_args()

    cfg = default_pot_config()
    mapper = ActionMapper(cfg)
    capture = ScreenCaptureWorker(cfg)
    controller = SafeInputController(cfg, mode=args.mode, enable_control=args.enable_control)

    root = tk.Tk()
    root.title("PALEO Overlay")
    root.geometry(f"420x190+{args.x}+{args.y}")
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    key_color = "#00ff00"
    root.configure(bg=key_color)
    try:
        root.wm_attributes("-transparentcolor", key_color)
    except Exception:
        root.attributes("-alpha", 0.88)

    panel = tk.Frame(root, bg="#101820", bd=1, relief="solid")
    panel.pack(fill="both", expand=True, padx=2, pady=2)
    title = tk.Label(panel, text="PALEO LIVE HUD", fg="#7ce0b8", bg="#101820", font=("Segoe UI", 11, "bold"))
    title.pack(anchor="w", padx=10, pady=(8, 0))
    text_var = tk.StringVar(value="starting...")
    body = tk.Label(
        panel,
        textvariable=text_var,
        fg="#eaf8f2",
        bg="#101820",
        justify="left",
        anchor="nw",
        font=("Consolas", 10),
    )
    body.pack(fill="both", expand=True, padx=10, pady=8)

    dt_ms = int(1000.0 / max(args.fps, 0.5))

    def tick() -> None:
        frame = capture.capture_once()
        obs = frame_to_observation(frame)
        result = simulate_instinct_decision(species=args.species, **obs)
        action = result["action"]
        keys = mapper.map_action(action)
        mouse_delta = mapper.map_mouse(action)
        ctrl = controller.execute_action(action, keys, mouse_delta=mouse_delta)
        payload = {
            "mode": args.mode,
            "control": args.enable_control,
            "frame": frame.frame_id,
            "src": frame.source,
            "motion": round(frame.motion_score, 4),
            "bright": round(frame.mean_brightness, 4),
            "action": action,
            "keys": list(keys),
            "mouse": list(mouse_delta),
            "status": ctrl.status,
        }
        text_var.set(json.dumps(payload, indent=2))
        if controller.emergency_stopped:
            text_var.set(text_var.get() + "\n\nEMERGENCY STOP ACTIVE (f12).")
            return
        root.after(dt_ms, tick)

    # Drag-to-move overlay.
    drag = {"x": 0, "y": 0}

    def on_down(event):
        drag["x"] = event.x_root
        drag["y"] = event.y_root

    def on_move(event):
        dx = event.x_root - drag["x"]
        dy = event.y_root - drag["y"]
        x = root.winfo_x() + dx
        y = root.winfo_y() + dy
        root.geometry(f"+{x}+{y}")
        drag["x"] = event.x_root
        drag["y"] = event.y_root

    panel.bind("<ButtonPress-1>", on_down)
    panel.bind("<B1-Motion>", on_move)
    root.bind("<Escape>", lambda _e: root.destroy())

    tick()
    root.mainloop()


if __name__ == "__main__":
    main()
