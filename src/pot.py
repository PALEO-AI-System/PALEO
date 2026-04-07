"""Path of Titans runtime assumptions, capture, and control scaffolding."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from time import time
from typing import Dict, List, Tuple

try:
    import numpy as np
except Exception:  # pragma: no cover - optional dependency
    np = None

try:
    import mss
except Exception:  # pragma: no cover - optional dependency
    mss = None

from .config import PotConfig, default_pot_config


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


class ScreenCaptureWorker:
    """Capture worker using mss if available, with graceful fallback."""

    def __init__(self, config: PotConfig | None = None) -> None:
        self.config = config or default_pot_config()
        self._next_frame_id = 1
        self._last_gray = None
        self._sct = mss.mss() if mss is not None else None

    def capture_once(self, timestamp_ms: int = 0) -> CaptureFrame:
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
        try:
            raw = self._sct.grab(monitor)
            arr = np.asarray(raw, dtype=np.uint8)  # BGRA
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
        )
        self._next_frame_id += 1
        return frame


def frame_to_observation(frame: CaptureFrame) -> Dict[str, float]:
    """Convert raw frame stats into normalized instinct inputs."""
    threat = max(0.0, min(1.0, frame.motion_score * 3.0 + max(0.0, frame.mean_brightness - 0.65) * 0.35))
    prey_density = max(0.0, min(1.0, 1.0 - abs(frame.mean_brightness - 0.5) * 2.0))
    stamina = max(0.2, min(1.0, 1.0 - threat * 0.6))
    return {
        "predator_probability": round(threat, 4),
        "prey_density": round(prey_density, 4),
        "health": 0.85,
        "stamina": round(stamina, 4),
        "hunger": 0.45,
        "thirst": 0.35,
    }


class ActionMapper:
    """Map high-level Instinct Agent actions to PoT key sequences."""

    def __init__(self, config: PotConfig | None = None) -> None:
        self.config = config or default_pot_config()

    def map_action(self, action: str) -> Tuple[str, ...]:
        return self.config.keymap.get(action, ())


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
