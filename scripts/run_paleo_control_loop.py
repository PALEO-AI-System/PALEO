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
import os
import sys
import time
from pathlib import Path

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
    classify_frame_predator_probability,
    frame_to_observation,
    primary_monitor_region,
)


def main() -> None:
    p = argparse.ArgumentParser(description="PALEO safe control loop (screen capture -> action -> optional input).")
    p.add_argument("--species", default="allosaurus")
    p.add_argument(
        "--brain",
        choices=["simulate", "local-rules", "local-model", "letta-api"],
        default="local-rules",
        help="Decision brain: simulate (legacy), local-rules, local-model, or letta-api fallback.",
    )
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
    p.add_argument(
        "--classifier-checkpoint",
        default="",
        help="Optional ResNet checkpoint for local-model threat perception.",
    )
    p.add_argument(
        "--letta-api-key-env",
        default="LETTA_API_KEY",
        help="Env var name containing Letta API key for letta-api mode.",
    )
    p.add_argument(
        "--letta-base-url-env",
        default="LETTA_BASE_URL",
        help="Env var name containing Letta API base URL.",
    )
    p.add_argument(
        "--letta-agent-id",
        default="",
        help="Optional Letta agent id override (falls back to LETTA_AGENT_ID).",
    )
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
    classifier_model = None
    classifier_device = None
    if args.classifier_checkpoint:
        try:
            classifier_model = load_classifier(args.classifier_checkpoint)
            classifier_device = torch.device("cuda" if (torch is not None and torch.cuda.is_available()) else "cpu")
            classifier_model = classifier_model.to(classifier_device)
            classifier_model.eval()
            print(f"Loaded classifier checkpoint: {args.classifier_checkpoint}")
        except Exception as exc:
            print(f"Classifier load failed ({args.classifier_checkpoint}): {exc}")
            classifier_model = None
            classifier_device = None

    dt = 1.0 / max(args.fps, 0.5)
    tick = 0
    recent_events: list[str] = []
    letta_key = os.getenv(args.letta_api_key_env, "")
    letta_base_url = os.getenv(args.letta_base_url_env, "")
    print(
        f"PALEO loop started source={args.input_source} brain={args.brain} mode={args.mode} "
        f"enable_control={args.enable_control} "
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
            obs = frame_to_observation(frame, classifier_model=classifier_model, classifier_device=classifier_device)
        else:
            obs = {
                "predator_probability": max(0.0, min(1.0, args.manual_threat)),
                "prey_density": max(0.0, min(1.0, args.manual_prey)),
                "health": max(0.0, min(1.0, args.manual_health)),
                "stamina": max(0.0, min(1.0, args.manual_stamina)),
                "hunger": max(0.0, min(1.0, args.manual_hunger)),
                "thirst": max(0.0, min(1.0, args.manual_thirst)),
            }

        model_predator_probability = None
        if (
            args.brain == "local-model"
            and frame is not None
            and classifier_model is not None
            and classifier_device is not None
            and frame.frame_bgr is not None
        ):
            try:
                model_predator_probability = classify_frame_predator_probability(
                    frame.frame_bgr, classifier_model, classifier_device
                )
            except Exception:
                model_predator_probability = None

        # Perceive -> Think -> Remember -> Decide -> Act
        decision = decide_with_brain(
            brain=args.brain,
            species=args.species,
            recent_events=recent_events,
            model_predator_probability=model_predator_probability,
            letta_api_key=letta_key,
            letta_base_url=letta_base_url,
            letta_agent_id=args.letta_agent_id,
            **obs,
        )
        action = decision["action"]
        keys = mapper.map_action(action)
        mouse_delta = mapper.map_mouse(action)
        mouse_clicks = mapper.map_mouse_clicks(action)
        result = controller.execute_action(
            action,
            keys,
            mouse_delta=mouse_delta,
            mouse_clicks=mouse_clicks,
        )
        recent_events.append(f"tick={tick}:action={action}:status={result.status}")
        if len(recent_events) > 24:
            recent_events = recent_events[-24:]

        row = {
            "tick": tick,
            "brain": args.brain,
            "frame_id": frame.frame_id if frame else 0,
            "source": frame.source if frame else "manual",
            "motion": frame.motion_score if frame else 0.0,
            "brightness": frame.mean_brightness if frame else 0.0,
            "obs": obs,
            "model_predator_probability": model_predator_probability,
            "action": action,
            "keys": keys,
            "mouse_delta": mouse_delta,
            "mouse_clicks": mouse_clicks,
            "control_status": result.status,
            "detail": result.detail,
            "thought_log": decision.get("thought_log", ""),
            "memory_events": len(recent_events),
            "snapshot": str(snap_path) if snap_path else "",
        }
        print(json.dumps(row, separators=(",", ":")))
        if controller.emergency_stopped:
            print("Emergency stop active. Exiting loop.")
            break
        time.sleep(dt)


if __name__ == "__main__":
    main()
