"""Transparent always-on-top PALEO overlay (screen sidecar).

Drag the green **drag bar** at the top to move the window (child widgets do not
forward drag events on all platforms).
"""

from __future__ import annotations

import argparse
import json
import sys
import tkinter as tk
from pathlib import Path
from tkinter import scrolledtext

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import default_pot_config
from src.letta_tools import simulate_instinct_decision
from src.pot import (
    ActionMapper,
    SafeInputController,
    ScreenCaptureWorker,
    frame_to_observation,
    primary_monitor_region,
)


def _bind_drag(widget: tk.Misc, root: tk.Tk, drag: dict) -> None:
    def on_down(event):
        drag["x"] = event.x_root
        drag["y"] = event.y_root

    def on_move(event):
        dx = event.x_root - drag["x"]
        dy = event.y_root - drag["y"]
        root.geometry(f"+{root.winfo_x() + dx}+{root.winfo_y() + dy}")
        drag["x"] = event.x_root
        drag["y"] = event.y_root

    widget.bind("<ButtonPress-1>", on_down)
    widget.bind("<B1-Motion>", on_move)


def main() -> None:
    p = argparse.ArgumentParser(description="PALEO transparent overlay HUD.")
    p.add_argument("--species", default="allosaurus")
    p.add_argument("--fps", type=float, default=4.0)
    p.add_argument("--mode", choices=["advice", "control"], default="advice")
    p.add_argument("--enable-control", action="store_true")
    p.add_argument("--x", type=int, default=24)
    p.add_argument("--y", type=int, default=24)
    p.add_argument("--compact", action="store_true", help="Shorter debug text.")
    p.add_argument(
        "--window-capture",
        action="store_true",
        help="Use fixed PotConfig region instead of full primary monitor.",
    )
    args = p.parse_args()

    if args.mode not in ("advice", "control"):
        args.mode = "advice"

    cfg = default_pot_config()
    if not args.window_capture:
        region = primary_monitor_region()
        if region is not None:
            cfg.capture_region = region

    mapper = ActionMapper(cfg)
    capture = ScreenCaptureWorker(cfg)
    controller = SafeInputController(cfg, mode=args.mode, enable_control=args.enable_control)

    root = tk.Tk()
    root.title("PALEO Overlay")
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    width = max(480, min(900, int(sw * 0.42)))
    height = max(280, min(560, int(sh * 0.38)))
    if args.compact:
        width = max(380, int(width * 0.78))
        height = max(220, int(height * 0.72))
    root.geometry(f"{width}x{height}+{args.x}+{args.y}")
    root.overrideredirect(True)
    root.attributes("-topmost", True)

    chroma = "#00ff00"
    root.configure(bg=chroma)
    try:
        root.wm_attributes("-transparentcolor", chroma)
    except tk.TclError:
        root.attributes("-alpha", 0.9)

    panel = tk.Frame(root, bg="#101820", bd=1, relief="solid")
    panel.pack(fill="both", expand=True, padx=2, pady=2)

    drag = {"x": 0, "y": 0}

    drag_bar = tk.Label(
        panel,
        text="  ≡ DRAG HERE to move  |  Esc=quit  |  +/- = font  |  Tab=toggle detail  ≡  ",
        fg="#0a1a14",
        bg=chroma,
        font=("Segoe UI", 8, "bold"),
        cursor="fleur",
    )
    drag_bar.pack(fill="x", side="top")
    _bind_drag(drag_bar, root, drag)
    _bind_drag(panel, root, drag)

    hint = tk.Label(
        panel,
        text="HUD shows: live capture stats → agent action → key/mouse preview → parsed thought + Letta stub trace (scroll)",
        fg="#6a8f84",
        bg="#101820",
        font=("Segoe UI", 7),
        wraplength=width - 40,
        justify="left",
    )
    hint.pack(anchor="w", padx=8, pady=(4, 0))

    status_var = tk.StringVar(value="starting...")
    status = tk.Label(
        panel,
        textvariable=status_var,
        fg="#9dd9c3",
        bg="#101820",
        justify="left",
        anchor="w",
        font=("Consolas", 8),
    )
    status.pack(fill="x", padx=8, pady=(4, 0))
    _bind_drag(status, root, drag)

    # Default body font smaller so more fits; user can +/- to zoom.
    default_font = 8
    state = {"verbose": not args.compact, "font": default_font}

    body = scrolledtext.ScrolledText(
        panel,
        fg="#eaf8f2",
        bg="#0c1418",
        insertbackground="#eaf8f2",
        wrap=tk.WORD,
        font=("Consolas", state["font"]),
        height=8,
        relief="flat",
        padx=6,
        pady=6,
    )
    body.pack(fill="both", expand=True, padx=8, pady=6)
    _bind_drag(body, root, drag)

    dt_ms = int(1000.0 / max(args.fps, 0.5))

    def set_font(sz: int) -> None:
        state["font"] = max(7, min(16, sz))
        body.configure(font=("Consolas", state["font"]))

    set_font(default_font)

    def tick() -> None:
        frame = capture.capture_once()
        obs = frame_to_observation(frame)
        result = simulate_instinct_decision(species=args.species, **obs)
        action = result["action"]
        keys = mapper.map_action(action)
        mouse_delta = mapper.map_mouse(action)
        ctrl = controller.execute_action(action, keys, mouse_delta=mouse_delta)

        thought_raw = result.get("thought_log") or ""
        thought_parsed = {}
        try:
            thought_parsed = json.loads(thought_raw) if thought_raw else {}
        except json.JSONDecodeError:
            thought_parsed = {"_parse_error": "thought_log not JSON", "raw_head": thought_raw[:400]}

        control_preview = {
            "keys": list(keys),
            "mouse_delta": list(mouse_delta),
            "executed_status": ctrl.status,
            "detail": ctrl.detail,
        }
        letta_trace = {
            "source": "local_tool_stub",
            "tool": "simulate_instinct_decision",
            "species": args.species,
            "note": "Real Letta ADE trace wired in a later step.",
        }

        region = list(frame.region)
        summary = {
            "capture_region_css": f"left,top,w,h = {region}",
            "frame_id": frame.frame_id,
            "src": frame.source,
            "error": frame.error,
            "motion": round(frame.motion_score, 4),
            "brightness": round(frame.mean_brightness, 4),
            "inputs_to_agent": obs,
            "action": action,
            "control_preview": control_preview,
            "letta_trace": letta_trace,
        }

        status_var.set(
            f"{action} | keys={list(keys)} mouse={list(mouse_delta)} | "
            f"motion={summary['motion']} bright={summary['brightness']} | {ctrl.status}"
        )

        lines = ["=== SUMMARY (debug) ===", json.dumps(summary, indent=2)]

        if state["verbose"]:
            lines.append("\n=== THOUGHT (parsed) ===")
            lines.append(json.dumps(thought_parsed, indent=2))
            lines.append("\n=== THOUGHT_RAW (truncated) ===")
            raw_show = thought_raw if len(thought_raw) <= 2500 else thought_raw[:2500] + "\n... [truncated]"
            lines.append(raw_show)
        else:
            dec = thought_parsed.get("decision") if isinstance(thought_parsed, dict) else {}
            if isinstance(dec, dict):
                lines.append(
                    "\n=== THOUGHT (short) ===\n"
                    + json.dumps(
                        {
                            "action": dec.get("action"),
                            "rationale": dec.get("rationale"),
                            "confidence": dec.get("confidence"),
                        },
                        indent=2,
                    )
                )

        text = "\n".join(lines)
        body.delete("1.0", tk.END)
        body.insert(tk.END, text)
        body.see("1.0")

        if controller.emergency_stopped:
            body.insert(tk.END, "\n\nEMERGENCY STOP (hold f12). Close overlay or restart.\n")
            return
        root.after(dt_ms, tick)

    def on_plus(_e=None):
        set_font(state["font"] + 1)

    def on_minus(_e=None):
        set_font(state["font"] - 1)

    def on_tab(_e=None):
        state["verbose"] = not state["verbose"]
        return "break"

    root.bind("<Escape>", lambda _e: root.destroy())
    root.bind("<plus>", on_plus)
    root.bind("<KP_Add>", on_plus)
    root.bind("<minus>", on_minus)
    root.bind("<KP_Subtract>", on_minus)
    root.bind("<Tab>", on_tab)

    tick()
    root.mainloop()


if __name__ == "__main__":
    main()
