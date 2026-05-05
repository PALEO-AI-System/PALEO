"""Transparent always-on-top PALEO overlay (screen sidecar).

Drag the **gradient title bar** to move. Toolbar buttons mirror common hotkeys.
"""

from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import json
import os
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import scrolledtext
try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None

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

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_XDOWN = 0x0080
MOUSEEVENTF_XUP = 0x0100
XBUTTON1 = 0x0001
XBUTTON2 = 0x0002


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
        "--demo-countdown-sec",
        type=int,
        default=3,
        help="Seconds to wait before starting Mock Demo actions.",
    )
    p.add_argument(
        "--demo-side-button",
        choices=["x1", "x2"],
        default="x1",
        help="Side mouse button to hold in mock demo sequence.",
    )
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
            text="Drag this bar to move  ·  Esc close  ·  F6 loop  ·  F7 demo  ·  F8 shot",
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
        "brain": args.brain,
        "mode": args.mode,
        "control_enabled": bool(args.enable_control),
        "demo_side_button": args.demo_side_button,
        "demo_countdown_sec": max(0, int(args.demo_countdown_sec)),
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
    btn_demo_water = tk.Button(toolbar, text="Water Demo")
    btn_demo_x1 = tk.Button(toolbar, text="Demo Side: X1")
    btn_demo_x2 = tk.Button(toolbar, text="Demo Side: X2")
    btn_help = tk.Button(toolbar, text="Workflow", command=toggle_help)
    btn_close = tk.Button(toolbar, text="Close", command=root.destroy)

    accent = "#2a5a50"
    accent_hi = "#3d7a6c"
    for b in (btn_smaller, btn_larger, btn_detail, btn_start, btn_stop, btn_snap, btn_demo, btn_demo_water, btn_demo_x1, btn_demo_x2, btn_help):
        _style_btn(b, accent, "#dff8f0", accent_hi)
    _style_btn(btn_close, "#5a3030", "#ffd0d0", "#7a4040")

    btn_smaller.pack(side=tk.LEFT, padx=(0, 4))
    btn_larger.pack(side=tk.LEFT, padx=(0, 8))
    btn_detail.pack(side=tk.LEFT, padx=(0, 8))
    btn_start.pack(side=tk.LEFT, padx=(0, 4))
    btn_stop.pack(side=tk.LEFT, padx=(0, 8))
    btn_snap.pack(side=tk.LEFT, padx=(0, 8))
    btn_demo.pack(side=tk.LEFT, padx=(0, 8))
    btn_demo_water.pack(side=tk.LEFT, padx=(0, 8))
    btn_demo_x1.pack(side=tk.LEFT, padx=(0, 4))
    btn_demo_x2.pack(side=tk.LEFT, padx=(0, 8))
    btn_help.pack(side=tk.LEFT, padx=(0, 8))
    btn_close.pack(side=tk.RIGHT)

    # Expose command-only runtime settings directly in UI.
    settings_row = tk.Frame(panel, bg="#0f181c")
    settings_row.pack(fill="x", padx=6, pady=(0, 4))
    settings = tk.Frame(settings_row, bg="#101a1e", highlightbackground="#2c4a43", highlightthickness=1)
    settings.pack(fill="x")

    brain_var = tk.StringVar(value=state["brain"])
    mode_var = tk.StringVar(value=state["mode"])
    side_var = tk.StringVar(value=state["demo_side_button"])
    countdown_var = tk.StringVar(value=str(state["demo_countdown_sec"]))
    control_var = tk.BooleanVar(value=state["control_enabled"])

    def _sync_runtime_settings(*_args) -> None:
        brain = brain_var.get().strip().lower()
        if brain in {"simulate", "local-rules", "local-model", "letta-api"}:
            state["brain"] = brain
        mode = mode_var.get().strip().lower()
        if mode in {"advice", "control"}:
            state["mode"] = mode
        controller.mode = state["mode"]
        state["control_enabled"] = bool(control_var.get())
        controller.enable_control = state["control_enabled"]
        side = side_var.get().strip().lower()
        state["demo_side_button"] = "x2" if side == "x2" else "x1"
        try:
            c = int(float(countdown_var.get().strip()))
        except Exception:
            c = state["demo_countdown_sec"]
        state["demo_countdown_sec"] = max(0, min(15, c))
        if countdown_var.get().strip() != str(state["demo_countdown_sec"]):
            countdown_var.set(str(state["demo_countdown_sec"]))

    tk.Label(settings, text="Brain", fg="#9cc4b8", bg="#101a1e", font=("Segoe UI", 7)).pack(side=tk.LEFT, padx=(8, 4), pady=4)
    tk.OptionMenu(settings, brain_var, "simulate", "local-rules", "local-model", "letta-api", command=lambda _v: _sync_runtime_settings()).pack(side=tk.LEFT, padx=(0, 8))
    tk.Label(settings, text="Mode", fg="#9cc4b8", bg="#101a1e", font=("Segoe UI", 7)).pack(side=tk.LEFT, padx=(0, 4))
    tk.OptionMenu(settings, mode_var, "advice", "control", command=lambda _v: _sync_runtime_settings()).pack(side=tk.LEFT, padx=(0, 8))
    tk.Checkbutton(
        settings,
        text="Enable control",
        variable=control_var,
        command=_sync_runtime_settings,
        fg="#b6d9cf",
        bg="#101a1e",
        selectcolor="#0f181c",
        activebackground="#101a1e",
        activeforeground="#dff8f0",
        font=("Segoe UI", 7),
    ).pack(side=tk.LEFT, padx=(0, 8))
    tk.Label(settings, text="Demo side", fg="#9cc4b8", bg="#101a1e", font=("Segoe UI", 7)).pack(side=tk.LEFT, padx=(0, 4))
    tk.OptionMenu(settings, side_var, "x1", "x2", command=lambda _v: _sync_runtime_settings()).pack(side=tk.LEFT, padx=(0, 8))
    tk.Label(settings, text="Countdown(s)", fg="#9cc4b8", bg="#101a1e", font=("Segoe UI", 7)).pack(side=tk.LEFT, padx=(0, 4))
    tk.Spinbox(
        settings,
        from_=0,
        to=15,
        width=4,
        textvariable=countdown_var,
        command=_sync_runtime_settings,
        font=("Segoe UI", 7),
    ).pack(side=tk.LEFT, padx=(0, 8))
    countdown_var.trace_add("write", lambda *_a: _sync_runtime_settings())
    _sync_runtime_settings()

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
        "Hotkeys: +/− font, Tab detail, F6 start/stop loop, F7 mock demo, F8 live shot, F12 emergency stop.\n"
        "Mock Demo supports both side buttons: X1 (near thumb) and X2 (forward thumb)."
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
        text="Scroll for full JSON · capture → perceive → decide → act · F6 loop · F7 demo · side: X1/X2 buttons · F8 snapshot · F12 stop",
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

    def run_mock_demo(side_button: str | None = None) -> None:
        if state["demo_running"]:
            _set_status("mock demo already running")
            return
        if keyboard is None:
            _set_status("mock demo unavailable: keyboard module missing")
            return

        def _demo_worker() -> None:
            state["demo_running"] = True
            countdown = max(0, int(state["demo_countdown_sec"]))
            for s in range(countdown, 0, -1):
                _set_status(f"mock demo starts in {s}s... switch focus to game")
                time.sleep(1.0)
            chosen_side_button = (side_button or state["demo_side_button"] or "x1").lower()
            _set_status(
                f"mock demo running... side={chosen_side_button} | mouse_module={'yes' if mouse is not None else 'no'}"
            )
            errors: list[str] = []

            def demo_log(msg: str) -> None:
                ts = dt.datetime.now().strftime("%H:%M:%S")
                print(f"[PALEO DEMO {ts}] {msg}", flush=True)

            def key_tap(key: str, hold_sec: float = 0.09) -> None:
                if keyboard is None:
                    errors.append(f"key:{key}:keyboard_missing")
                    return
                try:
                    demo_log(f"KEY TAP start key={key} hold={hold_sec:.2f}s")
                    keyboard.press(key)
                    time.sleep(hold_sec)
                    keyboard.release(key)
                    demo_log(f"KEY TAP done key={key}")
                except Exception as exc:
                    errors.append(f"key:{key}:{exc}")
                    demo_log(f"KEY TAP error key={key} err={exc}")

            def hold_keys(keys: list[str], duration_sec: float) -> None:
                if keyboard is None:
                    errors.append(f"keys_hold:{'+'.join(keys)}:keyboard_missing")
                    return
                pressed: list[str] = []
                try:
                    demo_log(f"KEY HOLD start keys={keys} dur={duration_sec:.2f}s")
                    for k in keys:
                        keyboard.press(k)
                        pressed.append(k)
                    time.sleep(max(0.0, float(duration_sec)))
                except Exception as exc:
                    errors.append(f"keys_hold:{'+'.join(keys)}:{exc}")
                    demo_log(f"KEY HOLD error keys={keys} err={exc}")
                finally:
                    for k in reversed(pressed):
                        try:
                            keyboard.release(k)
                        except Exception as exc:
                            errors.append(f"keys_release:{k}:{exc}")
                    demo_log(f"KEY HOLD done keys={keys}")

            def mouse_move_rel(dx: int, dy: int) -> None:
                moved = False
                if mouse is not None:
                    try:
                        demo_log(f"MOUSE MOVE try module dx={dx} dy={dy}")
                        mouse.move(dx, dy, absolute=False, duration=0)
                        moved = True
                    except Exception:
                        moved = False
                if not moved:
                    try:
                        demo_log(f"MOUSE MOVE fallback mouse_event dx={dx} dy={dy}")
                        ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE, int(dx), int(dy), 0, 0)
                        moved = True
                    except Exception as exc:
                        errors.append(f"mouse_move:{exc}")
                        demo_log(f"MOUSE MOVE error dx={dx} dy={dy} err={exc}")

            def mouse_click_btn(button: str) -> None:
                clicked = False
                if mouse is not None:
                    try:
                        demo_log(f"MOUSE CLICK try module button={button}")
                        mouse.click(button=button)
                        clicked = True
                    except Exception:
                        clicked = False
                if clicked:
                    demo_log(f"MOUSE CLICK done button={button} via module")
                    return
                try:
                    demo_log(f"MOUSE CLICK fallback button={button}")
                    if button == "left":
                        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                        time.sleep(0.08)
                        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                    elif button == "right":
                        ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                        time.sleep(0.04)
                        ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
                    elif button == "middle":
                        ctypes.windll.user32.mouse_event(MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
                        time.sleep(0.04)
                        ctypes.windll.user32.mouse_event(MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)
                    elif button in {"x", "x1"}:
                        ctypes.windll.user32.mouse_event(MOUSEEVENTF_XDOWN, 0, 0, XBUTTON1, 0)
                        time.sleep(0.04)
                        ctypes.windll.user32.mouse_event(MOUSEEVENTF_XUP, 0, 0, XBUTTON1, 0)
                    elif button == "x2":
                        ctypes.windll.user32.mouse_event(MOUSEEVENTF_XDOWN, 0, 0, XBUTTON2, 0)
                        time.sleep(0.04)
                        ctypes.windll.user32.mouse_event(MOUSEEVENTF_XUP, 0, 0, XBUTTON2, 0)
                    else:
                        errors.append(f"mouse_click:{button}:no_fallback")
                    demo_log(f"MOUSE CLICK done button={button} via fallback")
                except Exception as exc:
                    errors.append(f"mouse_click:{button}:{exc}")
                    demo_log(f"MOUSE CLICK error button={button} err={exc}")

            def mouse_press_btn(button: str) -> None:
                pressed = False
                if mouse is not None:
                    try:
                        demo_log(f"MOUSE PRESS try module button={button}")
                        mouse.press(button)
                        pressed = True
                    except Exception:
                        pressed = False
                if pressed:
                    demo_log(f"MOUSE PRESS done button={button} via module")
                    return
                try:
                    demo_log(f"MOUSE PRESS fallback button={button}")
                    if button in {"x", "x1"}:
                        ctypes.windll.user32.mouse_event(MOUSEEVENTF_XDOWN, 0, 0, XBUTTON1, 0)
                    elif button == "x2":
                        ctypes.windll.user32.mouse_event(MOUSEEVENTF_XDOWN, 0, 0, XBUTTON2, 0)
                    elif button == "left":
                        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                    elif button == "right":
                        ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                    elif button == "middle":
                        ctypes.windll.user32.mouse_event(MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
                    else:
                        errors.append(f"mouse_press:{button}:no_fallback")
                except Exception as exc:
                    errors.append(f"mouse_press:{button}:{exc}")
                    demo_log(f"MOUSE PRESS error button={button} err={exc}")

            def mouse_release_btn(button: str) -> None:
                released = False
                if mouse is not None:
                    try:
                        demo_log(f"MOUSE RELEASE try module button={button}")
                        mouse.release(button)
                        released = True
                    except Exception:
                        released = False
                if released:
                    demo_log(f"MOUSE RELEASE done button={button} via module")
                    return
                try:
                    demo_log(f"MOUSE RELEASE fallback button={button}")
                    if button in {"x", "x1"}:
                        ctypes.windll.user32.mouse_event(MOUSEEVENTF_XUP, 0, 0, XBUTTON1, 0)
                    elif button == "x2":
                        ctypes.windll.user32.mouse_event(MOUSEEVENTF_XUP, 0, 0, XBUTTON2, 0)
                    elif button == "left":
                        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                    elif button == "right":
                        ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
                    elif button == "middle":
                        ctypes.windll.user32.mouse_event(MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)
                except Exception as exc:
                    errors.append(f"mouse_release:{button}:{exc}")
                    demo_log(f"MOUSE RELEASE error button={button} err={exc}")

            try:
                # 0) Select slot/ability key first.
                key_tap("1")
                time.sleep(1.0)
                # 1) Move camera while holding W for ~5s.
                if keyboard is not None:
                    try:
                        keyboard.press("w")
                    except Exception as exc:
                        errors.append(f"key:w:press:{exc}")
                t_end = time.time() + 5.0
                while time.time() < t_end:
                    mouse_move_rel(130, 0)
                    time.sleep(0.12)
                if keyboard is not None:
                    try:
                        keyboard.release("w")
                    except Exception as exc:
                        errors.append(f"key:w:release:{exc}")
                # 1b) Hold W + LeftCtrl (2s), no mouse movement.
                hold_keys(["w", "left ctrl"], 2.0)
                # 1c) Hold W + D + Shift (3s), no mouse movement.
                hold_keys(["w", "d", "shift"], 3.0)
                # 2) Left click attack.
                mouse_click_btn("left")
                time.sleep(1.0)
                # 3) Hold side mouse button 2s while moving camera.
                demo_log(f"PRECISE STAGE start side_button={chosen_side_button}")
                mouse_press_btn(chosen_side_button)
                t_end = time.time() + 3.0
                while time.time() < t_end:
                    mouse_move_rel(140, 0)
                    time.sleep(0.10)
                mouse_release_btn(chosen_side_button)
                time.sleep(0.8)
                # 3b) Use the other side button for tail-attack style bind.
                other_side = "x2" if chosen_side_button == "x1" else "x1"
                demo_log(f"TAIL STAGE start side_button={other_side}")
                mouse_click_btn(other_side)
                time.sleep(1.0)
                # 4) Press R once, H twice.
                key_tap("r", hold_sec=0.16)
                time.sleep(1.2)
                # H sequence: press, hold, press with delays.
                key_tap("h")
                time.sleep(1.0)
                hold_keys(["h"], 2.0)
                time.sleep(3.0)
                key_tap("h")
                # Stand back up after H chain.
                time.sleep(0.9)
                key_tap("w", hold_sec=0.2)
                # Final mouse button chain at the end.
                time.sleep(0.9)
                mouse_click_btn("right")
                time.sleep(0.9)
                mouse_click_btn("middle")
                if errors:
                    _set_status(f"mock demo complete with warnings: {len(errors)} (see debug)")
                    body.insert(tk.END, "\n\n=== MOCK DEMO WARNINGS ===\n" + "\n".join(errors) + "\n")
                else:
                    _set_status("mock demo complete")
            except Exception as exc:
                _set_status(f"mock demo error: {exc}")
            finally:
                state["demo_running"] = False

        threading.Thread(target=_demo_worker, daemon=True).start()

    def run_water_demo() -> None:
        if state["demo_running"]:
            _set_status("another demo already running")
            return
        if keyboard is None:
            _set_status("water demo unavailable: keyboard module missing")
            return

        def _water_worker() -> None:
            state["demo_running"] = True
            errors: list[str] = []
            scan_phase = 1

            def demo_log(msg: str) -> None:
                ts = dt.datetime.now().strftime("%H:%M:%S")
                print(f"[PALEO WATER {ts}] {msg}", flush=True)

            countdown = max(0, int(state["demo_countdown_sec"]))
            for s in range(countdown, 0, -1):
                _set_status(f"water demo starts in {s}s... switch focus to game")
                time.sleep(1.0)
            _set_status(f"water demo running... mouse_module={'yes' if mouse is not None else 'no'}")
            demo_log(f"START mouse_module={'yes' if mouse is not None else 'no'} brain={state['brain']}")

            def key_tap(key: str, hold_sec: float = 0.1) -> None:
                try:
                    demo_log(f"KEY TAP start key={key} hold={hold_sec:.2f}s")
                    keyboard.press(key)
                    time.sleep(hold_sec)
                    keyboard.release(key)
                    demo_log(f"KEY TAP done key={key}")
                except Exception as exc:
                    errors.append(f"key_tap:{key}:{exc}")
                    demo_log(f"KEY TAP error key={key} err={exc}")

            def hold_keys(keys: list[str], duration_sec: float) -> None:
                pressed: list[str] = []
                try:
                    demo_log(f"KEY HOLD start keys={keys} dur={duration_sec:.2f}s")
                    for k in keys:
                        keyboard.press(k)
                        pressed.append(k)
                    time.sleep(max(0.0, float(duration_sec)))
                except Exception as exc:
                    errors.append(f"keys_hold:{'+'.join(keys)}:{exc}")
                    demo_log(f"KEY HOLD error keys={keys} err={exc}")
                finally:
                    for k in reversed(pressed):
                        try:
                            keyboard.release(k)
                        except Exception as exc:
                            errors.append(f"keys_release:{k}:{exc}")
                    demo_log(f"KEY HOLD done keys={keys}")

            def mouse_move_rel(dx: int, dy: int) -> None:
                moved = False
                if mouse is not None:
                    try:
                        demo_log(f"MOUSE MOVE try module dx={dx} dy={dy}")
                        mouse.move(dx, dy, absolute=False, duration=0)
                        moved = True
                    except Exception:
                        moved = False
                if not moved:
                    try:
                        demo_log(f"MOUSE MOVE fallback mouse_event dx={dx} dy={dy}")
                        ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE, int(dx), int(dy), 0, 0)
                    except Exception as exc:
                        errors.append(f"mouse_move:{exc}")
                        demo_log(f"MOUSE MOVE error dx={dx} dy={dy} err={exc}")

            def water_signal(frame_bgr: object) -> tuple[float, float]:
                """Return (blue_ratio, x_offset[-1..1]) as a simple water cue."""
                if np is None or frame_bgr is None:
                    return 0.0, 0.0
                arr = np.asarray(frame_bgr)
                if arr.ndim != 3 or arr.shape[2] < 3:
                    return 0.0, 0.0
                h, w = arr.shape[:2]
                # Focus the center-lower gameplay region, excluding most HUD lanes.
                y0 = int(h * 0.28)
                y1 = int(h * 0.78)
                x0 = int(w * 0.18)
                x1 = int(w * 0.82)
                roi = arr[y0:y1, x0:x1]
                if roi.size == 0:
                    return 0.0, 0.0
                b = roi[:, :, 0].astype(np.float32)
                g = roi[:, :, 1].astype(np.float32)
                r = roi[:, :, 2].astype(np.float32)
                blue_mask = (b > 78) & (b > g * 1.08) & (b > r * 1.08)
                ratio = float(blue_mask.mean())
                if ratio < 1e-4:
                    return ratio, 0.0
                xs = np.where(blue_mask)[1]
                cx = float(xs.mean()) / max(1.0, float(roi.shape[1] - 1))
                offset = max(-1.0, min(1.0, (cx - 0.5) * 2.0))
                return ratio, offset

            try:
                # Perception-guided seek/drink loop.
                t_end = time.time() + 30.0
                while time.time() < t_end:
                    frame = capture.capture_once()
                    obs = frame_to_observation(
                        frame,
                        classifier_model=classifier_model,
                        classifier_device=classifier_device,
                    )
                    decision = decide_with_brain(
                        brain=state["brain"],
                        species=args.species,
                        recent_events=recent_events,
                        letta_api_key=letta_key,
                        letta_base_url=letta_base_url,
                        letta_agent_id=args.letta_agent_id,
                        **obs,
                    )
                    action = str(decision.get("action") or "HOLD_POSITION")
                    thirst_now = float(obs.get("thirst", 1.0))
                    blue_ratio, blue_offset = water_signal(frame.frame_bgr)
                    demo_log(
                        f"TICK action={action} thirst={thirst_now:.3f} blue_ratio={blue_ratio:.3f} blue_offset={blue_offset:.2f}"
                    )
                    if thirst_now <= 0.08:
                        _set_status(f"water demo complete: thirst near full ({thirst_now:.3f})")
                        demo_log(f"DONE thirst_full thirst={thirst_now:.3f}")
                        break

                    # If we see strong water cue, drink attempt.
                    if blue_ratio >= 0.075 and action in {"SEEK_WATER", "FORAGE", "HOLD_POSITION", "EXPLORE"}:
                        hold_keys(["e"], 1.3)
                        time.sleep(0.5)
                        continue

                    # Offline-brain action-led control for water-seek stage.
                    if action in {"SEEK_WATER", "EXPLORE", "FORAGE", "HUNT", "FLEE", "FOLLOW_HERD"}:
                        steer_dx = int(max(-180, min(180, blue_offset * 240)))
                        if abs(steer_dx) < 20:
                            steer_dx = 85 * scan_phase
                            scan_phase *= -1
                        move_keys = ["w"]
                        if action == "FLEE":
                            move_keys = ["shift", "w"]
                        hold_keys(move_keys, 0.38)
                        mouse_move_rel(steer_dx, 0)
                        time.sleep(0.15)
                    else:
                        # If policy says to hold, briefly pause before next perception tick.
                        time.sleep(0.25)
                else:
                    _set_status("water demo finished (timeout) - check proximity to water")
                    demo_log("DONE timeout")

                if errors:
                    _set_status(f"water demo complete with warnings: {len(errors)} (see debug)")
                    body.insert(tk.END, "\n\n=== WATER DEMO WARNINGS ===\n" + "\n".join(errors) + "\n")
            except Exception as exc:
                _set_status(f"water demo error: {exc}")
            finally:
                state["demo_running"] = False

        threading.Thread(target=_water_worker, daemon=True).start()

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

    def toggle_loop() -> None:
        if state["loop_running"]:
            stop_loop()
        else:
            start_loop()

    btn_start.configure(command=start_loop)
    btn_stop.configure(command=stop_loop)
    btn_snap.configure(command=save_live_snapshot)
    btn_demo.configure(command=lambda: run_mock_demo(state["demo_side_button"]))
    btn_demo_water.configure(command=run_water_demo)
    btn_demo_x1.configure(command=lambda: run_mock_demo("x1"))
    btn_demo_x2.configure(command=lambda: run_mock_demo("x2"))

    action_history: list[dict[str, object]] = []

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
            brain=state["brain"],
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
        action_history.append(
            {
                "frame": frame.frame_id,
                "action": action,
                "keys": list(keys),
                "mouse_delta": list(mouse_delta),
                "mouse_clicks": list(mouse_clicks),
                "status": ctrl.status,
            }
        )
        if len(action_history) > 12:
            action_history[:] = action_history[-12:]
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
            "brain": state["brain"],
            "action": action,
            "control_preview": control_preview,
            "action_history_recent": action_history[-6:],
            "letta_trace": letta_trace,
        }

        decision_block = {}
        if isinstance(thought_parsed, dict):
            loop = thought_parsed.get("loop")
            if isinstance(loop, dict):
                decide = loop.get("decide")
                perceive = loop.get("perceive")
                if isinstance(decide, dict) and isinstance(perceive, dict):
                    decision_block = {
                        "perceive": perceive.get("obs", {}),
                        "decide": {
                            "action": decide.get("action"),
                            "rationale": decide.get("rationale"),
                            "confidence": decide.get("confidence"),
                        },
                    }

        _set_status(
            f"brain={state['brain']} mode={state['mode']} ctl={state['control_enabled']} | "
            f"action={action} | keys={list(keys)} | clicks={list(mouse_clicks)} | "
            f"mouse={list(mouse_delta)} | motion={summary['motion']} bright={summary['brightness']} | {ctrl.status}"
        )

        lines = [
            "=== LIVE PERCEIVE -> DECIDE -> ACT ===",
            json.dumps(
                {
                    "perception_inputs": obs,
                    "decision": decision_block.get("decide", {"action": action}),
                    "executed_controls": control_preview,
                    "recent_actions": action_history[-6:],
                },
                indent=2,
            ),
            "\n=== SUMMARY (debug) ===",
            json.dumps(summary, indent=2),
        ]

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

        scroll_pos = body.yview()[0]
        text = "\n".join(lines)
        body.delete("1.0", tk.END)
        body.insert(tk.END, text)
        if scroll_pos > 0.02:
            body.yview_moveto(scroll_pos)
        else:
            body.yview_moveto(0.0)

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

    def on_f6(_e=None):
        toggle_loop()
        return "break"

    def on_f7(_e=None):
        run_mock_demo()
        return "break"

    def on_f8(_e=None):
        save_live_snapshot()
        return "break"

    root.bind("<Escape>", lambda _e: root.destroy())
    root.bind("<plus>", on_plus)
    root.bind("<KP_Add>", on_plus)
    root.bind("<minus>", on_minus)
    root.bind("<KP_Subtract>", on_minus)
    root.bind("<Tab>", on_tab)
    root.bind("<F6>", on_f6)
    root.bind("<F7>", on_f7)
    root.bind("<F8>", on_f8)

    stop_loop()
    root.mainloop()


if __name__ == "__main__":
    main()
