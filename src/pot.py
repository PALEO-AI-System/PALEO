"""Path of Titans runtime assumptions, capture, and control scaffolding."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import ctypes
from pathlib import Path
from time import sleep
from time import time
from typing import Dict, List, Tuple
from .image_training import torch, transforms

try:
    import numpy as np
except Exception:  # pragma: no cover - optional dependency
    np = None

try:
    import mss
    import mss.tools as mss_tools
except Exception:  # pragma: no cover - optional dependency
    mss = None
    mss_tools = None

try:
    import keyboard
except Exception:  # pragma: no cover - optional dependency
    keyboard = None

try:
    import mouse
except Exception:  # pragma: no cover - optional dependency
    mouse = None

from .config import PotConfig, default_pot_config
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


def _mouse_event(flags: int, dx: int = 0, dy: int = 0, data: int = 0) -> None:
    ctypes.windll.user32.mouse_event(int(flags), int(dx), int(dy), int(data), 0)


def _fallback_mouse_move(dx: int, dy: int) -> None:
    _mouse_event(MOUSEEVENTF_MOVE, dx=dx, dy=dy)


def _fallback_mouse_click(button: str) -> bool:
    b = (button or "").lower()
    if b == "left":
        _mouse_event(MOUSEEVENTF_LEFTDOWN)
        sleep(0.02)
        _mouse_event(MOUSEEVENTF_LEFTUP)
        return True
    if b == "right":
        _mouse_event(MOUSEEVENTF_RIGHTDOWN)
        sleep(0.02)
        _mouse_event(MOUSEEVENTF_RIGHTUP)
        return True
    if b == "middle":
        _mouse_event(MOUSEEVENTF_MIDDLEDOWN)
        sleep(0.02)
        _mouse_event(MOUSEEVENTF_MIDDLEUP)
        return True
    if b in {"x", "x1"}:
        _mouse_event(MOUSEEVENTF_XDOWN, data=XBUTTON1)
        sleep(0.02)
        _mouse_event(MOUSEEVENTF_XUP, data=XBUTTON1)
        return True
    if b in {"x2"}:
        _mouse_event(MOUSEEVENTF_XDOWN, data=XBUTTON2)
        sleep(0.02)
        _mouse_event(MOUSEEVENTF_XUP, data=XBUTTON2)
        return True
    return False




@dataclass
class HudReadout:
    """Parsed HUD signals from a frame."""

    health: float
    stamina: float
    hunger: float
    thirst: float
    stamina_hidden_full: bool
    abilities_lane_visible: bool
    buffs_lane_visible: bool
    confidence: float


def primary_monitor_region() -> Tuple[int, int, int, int] | None:
    """Return (x, y, w, h) for primary monitor via mss."""
    if mss is None:
        return None
    try:
        with mss.mss() as sct:
            mon = sct.monitors[1]
            return (int(mon["left"]), int(mon["top"]), int(mon["width"]), int(mon["height"]))
    except Exception:
        return None


@dataclass
class CaptureFrame:
    """Single capture tick summary from the screen region."""

    frame_id: int
    region: Tuple[int, int, int, int]
    timestamp_ms: int
    width: int
    height: int
    mean_brightness: float
    motion_score: float
    source: str
    error: str = ""
    frame_bgr: object|None = None  # Optional raw frame 


class ScreenCaptureWorker:
    """Capture worker using mss if available, with graceful fallback."""

    def __init__(self, config: PotConfig | None = None) -> None:
        self.config = config or default_pot_config()
        self._next_frame_id = 1
        self._last_gray = None
        self._sct = mss.mss() if mss is not None else None

    def capture_once(self, timestamp_ms: int = 0, snapshot_path: str | Path | None = None) -> CaptureFrame:
        ts = timestamp_ms or int(time() * 1000)
        x, y, w, h = self.config.capture_region

        # Fallback mode when capture dependencies are missing.
        if self._sct is None or np is None:
            frame = CaptureFrame(
                frame_id=self._next_frame_id,
                region=self.config.capture_region,
                timestamp_ms=ts,
                width=w,
                height=h,
                mean_brightness=0.0,
                motion_score=0.0,
                source="fallback",
                error="mss_or_numpy_unavailable",
            )
            self._next_frame_id += 1
            return frame

        monitor = {"left": x, "top": y, "width": w, "height": h}
        frame_bgr = None
        try:
            raw = self._sct.grab(monitor)
            if snapshot_path:
                out = Path(snapshot_path)
                out.parent.mkdir(parents=True, exist_ok=True)
                if mss_tools is not None:
                    mss_tools.to_png(raw.rgb, raw.size, output=str(out))
            arr = np.asarray(raw, dtype=np.uint8)  # BGRA
            frame_bgr = arr[:, :, :3]              # Drop alpha channel if present  
            b = arr[:, :, 0].astype(np.float32)
            g = arr[:, :, 1].astype(np.float32)
            r = arr[:, :, 2].astype(np.float32)
            gray = 0.114 * b + 0.587 * g + 0.299 * r
            mean_brightness = float(gray.mean() / 255.0)
            if self._last_gray is None:
                motion_score = 0.0
            else:
                motion_score = float(np.abs(gray - self._last_gray).mean() / 255.0)
            self._last_gray = gray
        except Exception as exc:  # pragma: no cover - runtime hardware path
            frame = CaptureFrame(
                frame_id=self._next_frame_id,
                region=self.config.capture_region,
                timestamp_ms=ts,
                width=w,
                height=h,
                mean_brightness=0.0,
                motion_score=0.0,
                source="error",
                error=str(exc),
                frame_bgr=frame_bgr,
            )
            self._next_frame_id += 1
            return frame

        frame = CaptureFrame(
            frame_id=self._next_frame_id,
            region=self.config.capture_region,
            timestamp_ms=ts,
            width=w,
            height=h,
            mean_brightness=mean_brightness,
            motion_score=motion_score,
            source="mss",
            frame_bgr=frame_bgr,
        )
        self._next_frame_id += 1
        return frame


def _norm_roi(frame_bgr: object, x0: float, y0: float, x1: float, y1: float):
    if np is None:
        return None
    arr = np.asarray(frame_bgr)
    h, w = arr.shape[:2]
    ix0 = max(0, min(w - 1, int(x0 * w)))
    iy0 = max(0, min(h - 1, int(y0 * h)))
    ix1 = max(ix0 + 1, min(w, int(x1 * w)))
    iy1 = max(iy0 + 1, min(h, int(y1 * h)))
    return arr[iy0:iy1, ix0:ix1]


def parse_pot_hud(frame_bgr: object) -> HudReadout | None:
    """Parse core PoT HUD bars/icons from a frame.

    Layout assumptions are documented in docs/pot_hud_reference.md and use
    normalized bottom-center ROIs so this works across common resolutions.
    """
    if np is None or frame_bgr is None:
        return None
    arr = np.asarray(frame_bgr)
    if arr.ndim != 3 or arr.shape[2] < 3:
        return None

    # Health bar (red center bar).
    health_roi = _norm_roi(arr, 0.17, 0.79, 0.84, 0.84)
    # Stamina bar (white lane below health on left side only).
    stamina_roi = _norm_roi(arr, 0.18, 0.845, 0.44, 0.89)
    # Hunger/thirst icon ROIs.
    hunger_roi = _norm_roi(arr, 0.06, 0.76, 0.15, 0.93)
    thirst_roi = _norm_roi(arr, 0.85, 0.76, 0.94, 0.93)
    # Ability + buff lanes above health.
    abilities_roi = _norm_roi(arr, 0.36, 0.69, 0.66, 0.79)
    buffs_roi = _norm_roi(arr, 0.33, 0.61, 0.69, 0.69)

    if any(r is None for r in (health_roi, stamina_roi, hunger_roi, thirst_roi, abilities_roi, buffs_roi)):
        return None

    # BGR channels
    hb, hg, hr = health_roi[:, :, 0], health_roi[:, :, 1], health_roi[:, :, 2]
    sb, sg, sr = stamina_roi[:, :, 0], stamina_roi[:, :, 1], stamina_roi[:, :, 2]
    gb, gg, gr = hunger_roi[:, :, 0], hunger_roi[:, :, 1], hunger_roi[:, :, 2]
    tb, tg, tr = thirst_roi[:, :, 0], thirst_roi[:, :, 1], thirst_roi[:, :, 2]

    # Health: red dominance and brightness in bar lane.
    red_mask = (hr > 85) & (hr > hg * 1.25) & (hr > hb * 1.25)
    health = float(np.clip(red_mask.mean() * 1.18, 0.0, 1.0))

    # Stamina: white-ish dominance in lower-left lane.
    white_mask = (sr > 125) & (sg > 125) & (sb > 125) & (np.abs(sr - sg) < 35) & (np.abs(sg - sb) < 35)
    white_ratio = float(white_mask.mean())
    stamina_hidden_full = white_ratio < 0.03
    stamina = 1.0 if stamina_hidden_full else float(np.clip(white_ratio * 4.2, 0.0, 1.0))

    # Hunger icon (green), thirst icon (blue): require both mean dominance and
    # a minimum "active" pixel ratio so menu backgrounds are less likely to
    # masquerade as icon state.
    green_dom = gg.astype(np.float32) - (gr + gb) * 0.5
    blue_dom = tb.astype(np.float32) - (tr + tg) * 0.5
    green_active_ratio = float((green_dom > 18).mean())
    blue_active_ratio = float((blue_dom > 18).mean())
    green_strength = float(
        np.clip((((green_dom.mean() + 34.0) / 118.0) * (0.45 + 0.55 * green_active_ratio)), 0.0, 1.0)
    )
    blue_strength = float(
        np.clip((((blue_dom.mean() + 34.0) / 118.0) * (0.45 + 0.55 * blue_active_ratio)), 0.0, 1.0)
    )
    # Convert icon activity into need levels conservatively.
    hunger = float(np.clip(green_strength, 0.0, 1.0))
    thirst = float(np.clip(blue_strength, 0.0, 1.0))

    # Ability/buff lanes visibility confidence aids.
    abilities_gray = abilities_roi.mean(axis=2)
    buffs_gray = buffs_roi.mean(axis=2)
    abilities_lane_visible = bool(abilities_gray.mean() < 118 and abilities_gray.std() > 22)
    buffs_lane_visible = bool(buffs_gray.mean() < 122 and buffs_gray.std() > 18)

    # HUD anchor signal: at least some combination of expected HUD cues.
    icon_pair_present = green_active_ratio > 0.05 and blue_active_ratio > 0.05
    health_or_stamina_present = health > 0.07 or stamina_hidden_full or stamina > 0.12

    # Confidence increases when multiple lane signals agree.
    confidence_parts = [
        min(1.0, health / 0.8) if health > 0.02 else 0.18,
        0.85 if stamina_hidden_full or stamina > 0.05 else 0.22,
        0.85 if abilities_lane_visible else 0.25,
        0.8 if buffs_lane_visible else 0.25,
        0.95 if icon_pair_present else 0.20,
        0.9 if health_or_stamina_present else 0.22,
    ]
    confidence = float(np.clip(sum(confidence_parts) / len(confidence_parts), 0.0, 1.0))

    return HudReadout(
        health=round(float(health), 4),
        stamina=round(float(stamina), 4),
        hunger=round(float(hunger), 4),
        thirst=round(float(thirst), 4),
        stamina_hidden_full=stamina_hidden_full,
        abilities_lane_visible=abilities_lane_visible,
        buffs_lane_visible=buffs_lane_visible,
        confidence=round(confidence, 4),
    )


def frame_to_observation(
    frame: CaptureFrame,
    classifier_model=None,
    classifier_device=None,
) -> Dict[str, float]:
    """Convert raw frame stats into normalized instinct inputs."""

    heuristic_threat = max(0.0, min(1.0, frame.motion_score * 3.0 + max(0.0, frame.mean_brightness - 0.65) * 0.35))

    if classifier_model is not None and classifier_device is not None and frame.frame_bgr is not None:
        try:
            classifier_threat = classify_frame_predator_probability(
                frame.frame_bgr,
                classifier_model,
                classifier_device,
            )
            threat = max(heuristic_threat, classifier_threat)
        except Exception:
            threat = heuristic_threat
    else:
        threat = heuristic_threat

    prey_density = max(0.0, min(1.0, 1.0 - abs(frame.mean_brightness - 0.5) * 2.0))
    # Fallback vitals from scene-only heuristics.
    health = 0.85
    stamina = max(0.2, min(1.0, 1.0 - threat * 0.6))
    hunger = 0.45
    thirst = 0.35
    hud = parse_pot_hud(frame.frame_bgr) if frame.frame_bgr is not None else None
    if hud is not None and hud.confidence >= 0.55:
        # Blend parsed HUD values with conservative defaults.
        mix = min(0.75, max(0.35, hud.confidence))
        health = (1.0 - mix) * health + mix * hud.health
        stamina = (1.0 - mix) * stamina + mix * hud.stamina
        hunger = (1.0 - mix) * hunger + mix * hud.hunger
        thirst = (1.0 - mix) * thirst + mix * hud.thirst

    return {
        "predator_probability": round(threat, 4),
        "prey_density": round(prey_density, 4),
        "health": round(float(health), 4),
        "stamina": round(stamina, 4),
        "hunger": round(float(hunger), 4),
        "thirst": round(float(thirst), 4),
    }

def classify_frame_predator_probability(frame_bgr, model, device):
    """Return predator probability from a raw OpenCV BGR frame."""
    if torch is None or transforms is None:
        raise RuntimeError("torch + torchvision.transforms are required for classifier inference.")

    import cv2
    from PIL import Image

    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame_rgb)

    tfm = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ])

    x = tfm(img).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1)[0]
    return float(probs[1].item())  # class 1 = predator

@dataclass
class ControlResult:
    """Single input-control tick result."""

    ok: bool
    status: str
    action: str
    keys: Tuple[str, ...]
    mouse_delta: Tuple[int, int] = (0, 0)
    mouse_clicks: Tuple[str, ...] = ()
    detail: str = ""


class SafeInputController:
    """Rate-limited, kill-switch guarded keyboard control helper."""

    def __init__(
        self,
        config: PotConfig | None = None,
        *,
        mode: str = "advice",
        enable_control: bool = False,
        min_action_interval_sec: float = 0.35,
        key_hold_sec: float = 0.08,
    ) -> None:
        self.config = config or default_pot_config()
        self.mode = mode
        self.enable_control = enable_control
        self.min_action_interval_sec = float(min_action_interval_sec)
        self.key_hold_sec = float(key_hold_sec)
        self._last_action_at = 0.0
        self._emergency_stop = False

    @property
    def emergency_stopped(self) -> bool:
        return self._emergency_stop

    def poll_emergency_stop(self) -> bool:
        if keyboard is None:
            return self._emergency_stop
        try:
            if keyboard.is_pressed(self.config.emergency_stop_key):
                self._emergency_stop = True
        except Exception:
            pass
        return self._emergency_stop

    def clear_emergency_stop(self) -> None:
        self._emergency_stop = False

    def execute_action(
        self,
        action: str,
        keys: Tuple[str, ...],
        mouse_delta: Tuple[int, int] = (0, 0),
        mouse_clicks: Tuple[str, ...] = (),
    ) -> ControlResult:
        now = time()
        if self.poll_emergency_stop():
            return ControlResult(False, "blocked", action, keys, mouse_delta, mouse_clicks, "emergency_stop_active")
        if self.mode != "control":
            return ControlResult(True, "advice_only", action, keys, mouse_delta, mouse_clicks)
        if not self.enable_control:
            return ControlResult(True, "dry_run", action, keys, mouse_delta, mouse_clicks, "enable_control_false")
        if keyboard is None:
            return ControlResult(False, "blocked", action, keys, mouse_delta, mouse_clicks, "keyboard_module_missing")
        if now - self._last_action_at < self.min_action_interval_sec:
            return ControlResult(False, "rate_limited", action, keys, mouse_delta, mouse_clicks)
        if not keys and mouse_delta == (0, 0) and not mouse_clicks:
            return ControlResult(True, "noop", action, keys, mouse_delta, mouse_clicks)
        try:
            for k in keys:
                keyboard.press(k)
            sleep(self.key_hold_sec)
            for k in reversed(keys):
                keyboard.release(k)
            if mouse_delta != (0, 0):
                moved = False
                if mouse is not None:
                    try:
                        mouse.move(mouse_delta[0], mouse_delta[1], absolute=False, duration=0)
                        moved = True
                    except Exception:
                        moved = False
                if not moved:
                    _fallback_mouse_move(mouse_delta[0], mouse_delta[1])

            if mouse_clicks:
                for button in mouse_clicks:
                    if button not in {"left", "right", "middle", "x", "x1", "x2"}:
                        continue
                    clicked = False
                    if mouse is not None:
                        try:
                            mouse.click(button=button)
                            clicked = True
                        except Exception:
                            clicked = False
                    if not clicked:
                        _fallback_mouse_click(button)
            self._last_action_at = now
            return ControlResult(True, "executed", action, keys, mouse_delta, mouse_clicks)
        except Exception as exc:
            return ControlResult(False, "error", action, keys, mouse_delta, mouse_clicks, str(exc))


class ActionMapper:
    """Map high-level Instinct Agent actions to PoT key sequences."""

    def __init__(self, config: PotConfig | None = None) -> None:
        self.config = config or default_pot_config()

    def map_action(self, action: str) -> Tuple[str, ...]:
        return self.config.keymap.get(action, ())

    def map_mouse(self, action: str) -> Tuple[int, int]:
        return self.config.mousemap.get(action, (0, 0))

    def map_mouse_clicks(self, action: str) -> Tuple[str, ...]:
        return self.config.mouse_clickmap.get(action, ())


def describe_pot_integration_assumptions(config: PotConfig | None = None) -> Dict[str, object]:
    """Return explicit PoT integration assumptions from the plan."""
    cfg = config or default_pot_config()
    return {
        "target_window_title": cfg.target_window_title,
        "capture_region": cfg.capture_region,
        "target_fps": cfg.target_fps,
        "emergency_stop_key": cfg.emergency_stop_key,
        "keymap": cfg.keymap,
        "notes": [
            "Use borderless/windowed mode for deterministic capture region.",
            "Keep observe-decide-act loop in 5-10 FPS range initially.",
            "Require an immediate emergency-stop hotkey before enabling control loop.",
        ],
    }


def sample_action_mapping(actions: List[str]) -> Dict[str, Tuple[str, ...]]:
    """Map a list of actions for quick diagnostics."""
    mapper = ActionMapper()
    return {action: mapper.map_action(action) for action in actions}


def pot_config_as_dict(config: PotConfig | None = None) -> Dict[str, object]:
    """Serialize PotConfig for logs/API responses."""
    cfg = config or default_pot_config()
    return asdict(cfg)
