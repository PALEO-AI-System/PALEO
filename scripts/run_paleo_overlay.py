"""Transparent always-on-top PALEO overlay (screen sidecar)."""

from __future__ import annotations

import argparse
import json
import sys
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
    p.add_argument("--compact", action="store_true", help="Start in compact mode.")
    args = p.parse_args()

    cfg = default_pot_config()
    mapper = ActionMapper(cfg)
    capture = ScreenCaptureWorker(cfg)
    controller = SafeInputController(cfg, mode=args.mode, enable_control=args.enable_control)

    root = tk.Tk()
    root.title("PALEO Overlay")
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    width = max(520, min(820, int(sw * 0.38)))
    height = max(260, min(520, int(sh * 0.34)))
    if args.compact:
        width = max(420, int(width * 0.72))
        height = max(180, int(height * 0.66))
    root.geometry(f"{width}x{height}+{args.x}+{args.y}")
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
    title = tk.Label(
        panel,
        text="PALEO LIVE HUD  (drag to move, Esc close, +/- zoom, Tab compact)",
        fg="#7ce0b8",
        bg="#101820",
        font=("Segoe UI", 11, "bold"),
    )
    title.pack(anchor="w", padx=10, pady=(8, 0))
    status_var = tk.StringVar(value="starting...")
    status = tk.Label(
        panel,
        textvariable=status_var,
        fg="#9dd9c3",
        bg="#101820",
        justify="left",
        anchor="w",
        font=("Consolas", 10),
    )
    status.pack(fill="x", padx=10, pady=(6, 0))
    text_var = tk.StringVar(value="starting...")
    body = tk.Label(
        panel,
        textvariable=text_var,
        fg="#eaf8f2",
        bg="#101820",
        justify="left",
        anchor="nw",
        font=("Consolas", 12),
    )
    body.pack(fill="both", expand=True, padx=10, pady=8)

    dt_ms = int(1000.0 / max(args.fps, 0.5))
    state = {"compact": bool(args.compact), "font": 12}

    def set_font(size: int) -> None:
        state["font"] = max(8, min(20, size))
        body.configure(font=("Consolas", state["font"]))

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
        status_var.set(
            f"Action={action} | keys={list(keys)} | mouse={list(mouse_delta)} | "
            f"motion={payload['motion']} bright={payload['bright']}"
        )
        if state["compact"]:
            text_var.set(
                f"{action}\n"
                f"keys={list(keys)} mouse={list(mouse_delta)}\n"
                f"motion={payload['motion']} bright={payload['bright']} status={ctrl.status}"
            )
        else:
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

    def on_plus(_e=None):
        set_font(state["font"] + 1)

    def on_minus(_e=None):
        set_font(state["font"] - 1)

    def on_tab(_e=None):
        state["compact"] = not state["compact"]
        return "break"

    root.bind("<plus>", on_plus)
    root.bind("<KP_Add>", on_plus)
    root.bind("<minus>", on_minus)
    root.bind("<KP_Subtract>", on_minus)
    root.bind("<Tab>", on_tab)

    tick()
    root.mainloop()


if __name__ == "__main__":
    main()
