"""Path of Titans runtime assumptions and control scaffolding."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple

from .config import PotConfig, default_pot_config


@dataclass
class CaptureFrame:
    """Metadata-only frame placeholder for screen capture loops."""

    frame_id: int
    region: Tuple[int, int, int, int]
    timestamp_ms: int


class ScreenCaptureWorker:
    """Capture worker scaffold.

    This keeps the interface stable for future real capture backends (mss/pyautogui).
    """

    def __init__(self, config: PotConfig | None = None) -> None:
        self.config = config or default_pot_config()
        self._next_frame_id = 1

    def capture_once(self, timestamp_ms: int = 0) -> CaptureFrame:
        frame = CaptureFrame(
            frame_id=self._next_frame_id,
            region=self.config.capture_region,
            timestamp_ms=timestamp_ms,
        )
        self._next_frame_id += 1
        return frame


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
