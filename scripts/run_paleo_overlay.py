"""Transparent always-on-top PALEO overlay (screen sidecar).

Drag the **gradient title bar** to move. Toolbar buttons mirror common hotkeys.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import scrolledtext

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import default_pot_config
from src.image_training import load_classifier, torch
from src.letta_tools import decide_with_brain
from src.pot import (
    ActionMapper,
    SafeInputController,
    ScreenCaptureWorker,
    frame_to_observation,
    keyboard,
    mouse,
    primary_monitor_region,
)


def _hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_hex(r: float, g: float, b: float) -> str:
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def _paint_gradient(canvas: tk.Canvas, w: int, h: int, top: str, bottom: str) -> None:
    canvas.delete("grad")
    r1, g1, b1 = _hex_rgb(top)
    r2, g2, b2 = _hex_rgb(bottom)
    hm = max(h - 1, 1)
    for i in range(h):
        t = i / hm
        r = r1 + (r2 - r1) * t
        g = g1 + (g2 - g1) * t
        b = b1 + (b2 - b1) * t
        canvas.create_line(0, i, w, i, fill=_rgb_hex(r, g, b), tags="grad")


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


def _style_btn(w: tk.Misc, bg: str, fg: str, active: str) -> None:
    w.configure(
        bg=bg,
        fg=fg,
        activebackground=active,
        activeforeground=fg,
        relief=tk.FLAT,
        bd=0,
        padx=10,
        pady=4,
        cursor="hand2",
        font=("Segoe UI", 7, "bold"),
    )


def main() -> None:
    p = argparse.ArgumentParser(description="PALEO transparent overlay HUD.")
    p.add_argument("--species", default="allosaurus")
    p.add_argument("--brain", choices=["simulate", "local-rules", "local-model", "letta-api"], default="local-rules")
    p.add_argument("--fps", type=float, default=4.0)
    p.add_argument("--mode", choices=["advice", "control"], default="advice")
    p.add_argument("--enable-control", action="store_true")
    p.add_argument("--x", type=int, default=24)
    p.add_argument("--y", type=int, default=24)
    p.add_argument("--compact", action="store_true", help="Shorter debug text.")
    p.add_argument(
        "--classifier-checkpoint",
        default=None,
        help="Optional path to a trained classifier checkpoint (.pt).",
    )
    p.add_argument("--letta-agent-id", default="", help="Optional Letta agent id override.")
    p.add_argument("--letta-api-key-env", default="LETTA_API_KEY")
    p.add_argument("--letta-base-url-env", default="LETTA_BASE_URL")
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
    classifier_model = None
    classifier_device = None
    classifier_error = ""
    if args.classifier_checkpoint:
        try:
            classifier_model = load_classifier(args.classifier_checkpoint)
            if torch is None:
                raise RuntimeError("torch is unavailable.")
            classifier_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            classifier_model = classifier_model.to(classifier_device)
            classifier_model.eval()
        except Exception as exc:
            classifier_model = None
            classifier_device = None
            classifier_error = str(exc)

    root = tk.Tk()
    root.title("PALEO Overlay")
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    width = max(520, min(920, int(sw * 0.44)))
    height = max(320, min(620, int(sh * 0.42)))
    if args.compact:
        width = max(400, int(width * 0.82))
        height = max(240, int(height * 0.75))
    root.geometry(f"{width}x{height}+{args.x}+{args.y}")
    root.overrideredirect(True)
    root.attributes("-topmost", True)

    chroma = "#00ff00"
    root.configure(bg=chroma)
    try:
        root.wm_attributes("-transparentcolor", chroma)
    except tk.TclError:
        root.attributes("-alpha", 0.92)

    # Bordered shell: outer rim visible against any backdrop
    shell = tk.Frame(root, bg=chroma, highlightthickness=0)
    shell.pack(fill="both", expand=True, padx=3, pady=3)
    rim = tk.Frame(
        shell,
        bg="#1c2e28",
        highlightbackground="#5bc4a8",
        highlightthickness=2,
        highlightcolor="#7dffe0",
    )
    rim.pack(fill="both", expand=True)

    panel = tk.Frame(rim, bg="#0a1014", bd=0)
    panel.pack(fill="both", expand=True, padx=2, pady=2)

    drag = {"x": 0, "y": 0}

    title_wrap = tk.Frame(panel, bg="#0a1014")
    title_wrap.pack(fill="x", side="top")

    title_canvas = tk.Canvas(
        title_wrap,
        height=52,
        highlightthickness=0,
        bd=0,
        cursor="fleur",
    )
    title_canvas.pack(fill="x")

    def redraw_title(_event=None):
        title_canvas.update_idletasks()
        tw = max(title_canvas.winfo_width(), 2)
        th = 52
        title_canvas.config(height=th)
        _paint_gradient(title_canvas, tw, th, "#0d3d35", "#1a6b5c")
        title_canvas.delete("title")
        title_canvas.create_text(
            12,
            14,
            anchor="w",
            text="PALEO · live overlay",
            fill="#e8fff8",
            font=("Segoe UI", 9, "bold"),
            tags="title",
        )
        title_canvas.create_text(
            12,
            34,
            anchor="w",
            text="Drag this bar to move  ·  Esc close",
            fill="#a8e0d4",
            font=("Segoe UI", 7),
            tags="title",
        )

    title_canvas.bind("<Configure>", lambda e: redraw_title())
    _bind_drag(title_canvas, root, drag)

    toolbar = tk.Frame(panel, bg="#0f181c")
    toolbar.pack(fill="x", padx=6, pady=(0, 4))

    default_font = 7
    state = {
        "verbose": not args.compact,
        "font": default_font,
        "help_open": False,
        "loop_running": False,
        "loop_job": None,
        "demo_running": False,
    }

    def set_font(sz: int) -> None:
        state["font"] = max(6, min(14, sz))
        body.configure(font=("Consolas", state["font"]))
        status.configure(font=("Consolas", state["font"]))

    def toggle_verbose() -> None:
        state["verbose"] = not state["verbose"]
        btn_detail.configure(text="Detail: on" if state["verbose"] else "Detail: off")

    def toggle_help() -> None:
        state["help_open"] = not state["help_open"]
        if state["help_open"]:
            help_frame.pack(fill="x", padx=6, pady=(0, 4), before=status_master)
            btn_help.configure(text="Hide workflow")
        else:
            help_frame.pack_forget()
            btn_help.configure(text="Workflow")

    btn_smaller = tk.Button(toolbar, text="A−", command=lambda: set_font(state["font"] - 1))
    btn_larger = tk.Button(toolbar, text="A+", command=lambda: set_font(state["font"] + 1))
    btn_detail = tk.Button(toolbar, text="Detail: on" if state["verbose"] else "Detail: off", command=toggle_verbose)
    btn_start = tk.Button(toolbar, text="Start Loop")
    btn_stop = tk.Button(toolbar, text="Stop Loop")
    btn_snap = tk.Button(toolbar, text="Live Feed Shot")
    btn_demo = tk.Button(toolbar, text="Mock Demo")
    btn_help = tk.Button(toolbar, text="Workflow", command=toggle_help)
    btn_close = tk.Button(toolbar, text="Close", command=root.destroy)

    accent = "#2a5a50"
    accent_hi = "#3d7a6c"
    for b in (btn_smaller, btn_larger, btn_detail, btn_start, btn_stop, btn_snap, btn_demo, btn_help):
        _style_btn(b, accent, "#dff8f0", accent_hi)
    _style_btn(btn_close, "#5a3030", "#ffd0d0", "#7a4040")

    btn_smaller.pack(side=tk.LEFT, padx=(0, 4))
    btn_larger.pack(side=tk.LEFT, padx=(0, 8))
    btn_detail.pack(side=tk.LEFT, padx=(0, 8))
    btn_start.pack(side=tk.LEFT, padx=(0, 4))
    btn_stop.pack(side=tk.LEFT, padx=(0, 8))
    btn_snap.pack(side=tk.LEFT, padx=(0, 8))
    btn_demo.pack(side=tk.LEFT, padx=(0, 8))
    btn_help.pack(side=tk.LEFT, padx=(0, 8))
    btn_close.pack(side=tk.RIGHT)

    help_frame = tk.Frame(panel, bg="#0d1618", highlightbackground="#3d5a52", highlightthickness=1)
    workflow_txt = (
        "PALEO workflow (exe / dev):\n"
        "1) PALEO.exe — starts the local server and opens the browser Companion HUD "
        "(Instinct Agent ticks + optional live screen stats).\n"
        "2) PALEOOverlay.exe — this window: always-on-top debug beside your game; "
        "same capture + stub agent; optional keyboard/mouse only if you run the "
        "control loop with --enable-control (F12 emergency stop).\n"
        "3) For training/models use the Python scripts from README; Letta ADE hooks "
        "are not required for this HUD to run.\n"
        "Hotkeys: +/− font, Tab toggles verbose debug (same as Detail button)."
    )
    tk.Label(
        help_frame,
        text=workflow_txt,
        fg="#9cc4b8",
        bg="#0d1618",
        justify="left",
        anchor="nw",
        font=("Segoe UI", 7),
        wraplength=width - 36,
    ).pack(fill="x", padx=8, pady=6)

    status_master = tk.Frame(panel, bg="#0a1014")
    status_master.pack(fill="x", padx=6, pady=(2, 0))

    status_var = tk.StringVar(value="starting…")
    status = tk.Label(
        status_master,
        textvariable=status_var,
        fg="#7dd4c4",
        bg="#0a1014",
        justify="left",
        anchor="nw",
        font=("Consolas", default_font),
    )
    status.pack(fill="x", anchor="w")
    if classifier_error:
        status_var.set(f"classifier disabled: {classifier_error}")

    def on_panel_configure(event):
        if event.widget is panel:
            inner = max(event.width - 24, 80)
            status.configure(wraplength=inner)

    panel.bind("<Configure>", on_panel_configure)

    hint = tk.Label(
        panel,
        text="Scroll for full JSON · capture → agent → keys/mouse · Letta trace stub",
        fg="#5a7a72",
        bg="#0a1014",
        font=("Segoe UI", 6),
        wraplength=width - 24,
        justify="left",
    )
    hint.pack(anchor="w", padx=8, pady=(2, 0))

    body = scrolledtext.ScrolledText(
        panel,
        fg="#d8ebe4",
        bg="#060a0c",
        insertbackground="#d8ebe4",
        wrap=tk.WORD,
        font=("Consolas", state["font"]),
        height=10,
        relief=tk.FLAT,
        padx=8,
        pady=8,
        highlightthickness=1,
        highlightbackground="#2a4540",
        highlightcolor="#4a8070",
    )
    body.pack(fill="both", expand=True, padx=6, pady=(4, 8))
    _bind_drag(body, root, drag)

    set_font(default_font)
    redraw_title()

    dt_ms = int(1000.0 / max(args.fps, 0.5))
    recent_events: list[str] = []
    letta_key = os.getenv(args.letta_api_key_env, "")
    letta_base_url = os.getenv(args.letta_base_url_env, "")

    def _set_status(msg: str) -> None:
        status_var.set(msg)

    def _downloads_dir() -> Path:
        home = Path.home()
        dl = home / "Downloads"
        if dl.exists():
            return dl
        return home

    def save_live_snapshot() -> None:
        ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        out = _downloads_dir() / f"paleo_overlay_live_{ts}.png"
        frame = capture.capture_once(snapshot_path=out)
        _set_status(f"snapshot saved: {out} | frame={frame.frame_id}")
        try:
            os.startfile(str(out))  # type: ignore[attr-defined]
        except Exception:
            pass

    def run_mock_demo() -> None:
        if state["demo_running"]:
            _set_status("mock demo already running")
            return
        if args.mode != "control" or not args.enable_control:
            _set_status("mock demo requires --mode control --enable-control")
            return
        if keyboard is None or mouse is None:
            _set_status("mock demo unavailable: keyboard/mouse module missing")
            return

        def _demo_worker() -> None:
            state["demo_running"] = True
            _set_status("mock demo running...")
            try:
                # 0) Select slot/ability key first.
                keyboard.press_and_release("1")
                time.sleep(0.12)
                # 1) Move camera while holding W for ~5s.
                keyboard.press("w")
                t_end = time.time() + 5.0
                while time.time() < t_end:
                    mouse.move(16, 0, absolute=False, duration=0)
                    time.sleep(0.2)
                keyboard.release("w")
                # 2) Left click attack.
                mouse.click("left")
                # 3) Hold side button 2s while moving camera.
                mouse.press("x")
                t_end = time.time() + 2.0
                while time.time() < t_end:
                    mouse.move(12, 0, absolute=False, duration=0)
                    time.sleep(0.2)
                mouse.release("x")
                # 4) Press R once, H twice.
                keyboard.press_and_release("r")
                keyboard.press_and_release("h")
                time.sleep(0.12)
                keyboard.press_and_release("h")
                _set_status("mock demo complete")
            except Exception as exc:
                _set_status(f"mock demo error: {exc}")
            finally:
                state["demo_running"] = False

        threading.Thread(target=_demo_worker, daemon=True).start()

    def stop_loop() -> None:
        state["loop_running"] = False
        job = state.get("loop_job")
        if job is not None:
            try:
                root.after_cancel(job)
            except Exception:
                pass
        state["loop_job"] = None
        _set_status("loop stopped; manual controls available")

    def start_loop() -> None:
        if state["loop_running"]:
            _set_status("loop already running")
            return
        state["loop_running"] = True
        _set_status("loop started")
        tick()

    btn_start.configure(command=start_loop)
    btn_stop.configure(command=stop_loop)
    btn_snap.configure(command=save_live_snapshot)
    btn_demo.configure(command=run_mock_demo)

    def tick() -> None:
        if not state["loop_running"]:
            return
        frame = capture.capture_once()
        obs = frame_to_observation(
            frame,
            classifier_model=classifier_model,
            classifier_device=classifier_device,
        )
        result = decide_with_brain(
            brain=args.brain,
            species=args.species,
            recent_events=recent_events,
            letta_api_key=letta_key,
            letta_base_url=letta_base_url,
            letta_agent_id=args.letta_agent_id,
            **obs,
        )
        action = result["action"]
        keys = mapper.map_action(action)
        mouse_delta = mapper.map_mouse(action)
        mouse_clicks = mapper.map_mouse_clicks(action)
        ctrl = controller.execute_action(
            action,
            keys,
            mouse_delta=mouse_delta,
            mouse_clicks=mouse_clicks,
        )
        recent_events.append(f"frame={frame.frame_id}:action={action}:status={ctrl.status}")
        if len(recent_events) > 24:
            recent_events[:] = recent_events[-24:]

        thought_raw = result.get("thought_log") or ""
        thought_parsed: dict
        try:
            thought_parsed = json.loads(thought_raw) if thought_raw else {}
        except json.JSONDecodeError:
            thought_parsed = {"_parse_error": "thought_log not JSON", "raw_head": thought_raw[:400]}

        control_preview = {
            "keys": list(keys),
            "mouse_delta": list(mouse_delta),
            "mouse_clicks": list(mouse_clicks),
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
            "brain": args.brain,
            "action": action,
            "control_preview": control_preview,
            "letta_trace": letta_trace,
        }

        _set_status(
            f"action={action}  |  keys={list(keys)}  |  mouse={list(mouse_delta)}  |  "
            f"motion={summary['motion']}  bright={summary['brightness']}  |  {ctrl.status}"
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
            state["loop_running"] = False
            return
        state["loop_job"] = root.after(dt_ms, tick)

    def on_plus(_e=None):
        set_font(state["font"] + 1)

    def on_minus(_e=None):
        set_font(state["font"] - 1)

    def on_tab(_e=None):
        toggle_verbose()
        return "break"

    root.bind("<Escape>", lambda _e: root.destroy())
    root.bind("<plus>", on_plus)
    root.bind("<KP_Add>", on_plus)
    root.bind("<minus>", on_minus)
    root.bind("<KP_Subtract>", on_minus)
    root.bind("<Tab>", on_tab)

    stop_loop()
    root.mainloop()


if __name__ == "__main__":
    main()
