"""Run a safe local control loop from live screen capture to action output.

V1 goals:
- live capture (no game API)
- optional periodic screenshots
- advice-only by default
- guarded control mode with emergency-stop key
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

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


def main() -> None:
    p = argparse.ArgumentParser(description="PALEO safe control loop (screen capture -> action -> optional input).")
    p.add_argument("--species", default="allosaurus")
    p.add_argument(
        "--input-source",
        choices=["live", "manual"],
        default="live",
        help="Use live screen capture stats or fixed manual values.",
    )
    p.add_argument("--mode", choices=["advice", "control"], default="advice")
    p.add_argument(
        "--enable-control",
        action="store_true",
        help="Actually send keyboard inputs (requires --mode control).",
    )
    p.add_argument("--ticks", type=int, default=0, help="0 means run forever.")
    p.add_argument("--fps", type=float, default=4.0)
    p.add_argument(
        "--full-screen",
        action="store_true",
        help="Capture full primary monitor (live source only).",
    )
    p.add_argument(
        "--snapshot-every",
        type=int,
        default=0,
        help="Save one PNG every N ticks (0 disables).",
    )
    p.add_argument(
        "--snapshot-dir",
        default="results/live_capture_snaps",
        help="Directory for periodic screenshots.",
    )
    p.add_argument("--manual-threat", type=float, default=0.35)
    p.add_argument("--manual-prey", type=float, default=0.4)
    p.add_argument("--manual-health", type=float, default=0.85)
    p.add_argument("--manual-stamina", type=float, default=0.75)
    p.add_argument("--manual-hunger", type=float, default=0.45)
    p.add_argument("--manual-thirst", type=float, default=0.35)
    args = p.parse_args()

    cfg = default_pot_config()
    if args.input_source == "live" and args.full_screen:
        region = primary_monitor_region()
        if region is not None:
            cfg.capture_region = region
    mapper = ActionMapper(cfg)
    capture = ScreenCaptureWorker(cfg)
    controller = SafeInputController(
        cfg,
        mode=args.mode,
        enable_control=args.enable_control,
    )

    dt = 1.0 / max(args.fps, 0.5)
    tick = 0
    print(
        f"PALEO loop started source={args.input_source} mode={args.mode} enable_control={args.enable_control} "
        f"fps={args.fps} emergency_key={cfg.emergency_stop_key}"
    )
    while True:
        tick += 1
        if args.ticks and tick > args.ticks:
            break
        snap_path = None
        if args.snapshot_every > 0 and tick % args.snapshot_every == 0:
            snap_path = Path(args.snapshot_dir) / f"frame_{tick:06d}.png"
        frame = capture.capture_once(snapshot_path=snap_path) if args.input_source == "live" else None
        if frame is not None:
            obs = frame_to_observation(frame)
        else:
            obs = {
                "predator_probability": max(0.0, min(1.0, args.manual_threat)),
                "prey_density": max(0.0, min(1.0, args.manual_prey)),
                "health": max(0.0, min(1.0, args.manual_health)),
                "stamina": max(0.0, min(1.0, args.manual_stamina)),
                "hunger": max(0.0, min(1.0, args.manual_hunger)),
                "thirst": max(0.0, min(1.0, args.manual_thirst)),
            }
        decision = simulate_instinct_decision(species=args.species, **obs)
        action = decision["action"]
        keys = mapper.map_action(action)
        mouse_delta = mapper.map_mouse(action)
        result = controller.execute_action(action, keys, mouse_delta=mouse_delta)

        row = {
            "tick": tick,
            "frame_id": frame.frame_id if frame else 0,
            "source": frame.source if frame else "manual",
            "motion": frame.motion_score if frame else 0.0,
            "brightness": frame.mean_brightness if frame else 0.0,
            "action": action,
            "keys": keys,
            "mouse_delta": mouse_delta,
            "control_status": result.status,
            "detail": result.detail,
            "snapshot": str(snap_path) if snap_path else "",
        }
        print(json.dumps(row, separators=(",", ":")))
        if controller.emergency_stopped:
            print("Emergency stop active. Exiting loop.")
            break
        time.sleep(dt)


if __name__ == "__main__":
    main()
