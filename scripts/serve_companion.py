"""Serve PALEO static pages plus JSON APIs for the local Companion HUD.

Run from repository root. Open the HUD at /companion-hud.html — do not open as a
file:// URL, or fetch() to /api/* will fail.

Example:
    python scripts/serve_companion.py
    python scripts/serve_companion.py --port 8765
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

# Allow `python scripts/serve_companion.py` without PYTHONPATH tweaks.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.letta_tools import get_species_fast_facts, simulate_instinct_decision  # noqa: E402
from src.pot import ScreenCaptureWorker, frame_to_observation  # noqa: E402


def _float(qs: dict[str, list[str]], key: str, default: float) -> float:
    raw = (qs.get(key) or [str(default)])[0]
    try:
        return float(raw)
    except ValueError:
        return default


def _metrics_payload(project_root: Path) -> dict[str, object]:
    path = project_root / "results" / "experiments" / "default_run" / "metrics.json"
    if not path.is_file():
        return {"ok": False, "error": "metrics.json not found", "path": str(path)}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"invalid json: {exc}", "path": str(path)}
    return {"ok": True, "metrics": data, "path": str(path)}


def _species_ids(project_root: Path) -> list[str]:
    instinct = project_root / "configs" / "instinct"
    if not instinct.is_dir():
        return []
    return sorted(p.stem for p in instinct.glob("*.json"))


def make_handler(project_root: Path, pages_dir: Path, live_capture: bool = False):
    capture_worker = ScreenCaptureWorker() if live_capture else None

    class CompanionRequestHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(pages_dir), **kwargs)

        def log_message(self, fmt: str, *args) -> None:
            sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), fmt % args))

        def end_headers(self) -> None:
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            path = unquote(parsed.path)

            if path == "/api/species":
                self._send_json({"species": _species_ids(project_root)})
                return
            if path == "/api/metrics":
                self._send_json(_metrics_payload(project_root))
                return
            if path == "/api/hud":
                self._api_hud(parse_qs(parsed.query))
                return

            super().do_GET()

        def _send_json(self, obj: object, status: int = 200) -> None:
            raw = json.dumps(obj, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def _api_hud(self, qs: dict[str, list[str]]) -> None:
            species_list = _species_ids(project_root)
            default_species = species_list[0] if species_list else "kto_pachyrhinosaurus"
            species = (qs.get("species") or [default_species])[0].strip() or default_species

            use_live = capture_worker is not None and (qs.get("use_live") or ["1"])[0] != "0"
            live_frame = None
            if use_live:
                live_frame = capture_worker.capture_once(timestamp_ms=int(time.time() * 1000))
                obs = frame_to_observation(live_frame)
                predator_probability = obs["predator_probability"]
                prey_density = obs["prey_density"]
                health = obs["health"]
                stamina = obs["stamina"]
                hunger = obs["hunger"]
                thirst = obs["thirst"]
            else:
                predator_probability = max(0.0, min(1.0, _float(qs, "predator_probability", 0.35)))
                prey_density = max(0.0, min(1.0, _float(qs, "prey_density", 0.4)))
                health = max(0.0, min(1.0, _float(qs, "health", 0.85)))
                stamina = max(0.0, min(1.0, _float(qs, "stamina", 0.75)))
                hunger = max(0.0, min(1.0, _float(qs, "hunger", 0.45)))
                thirst = max(0.0, min(1.0, _float(qs, "thirst", 0.35)))

            result = simulate_instinct_decision(
                species=species,
                predator_probability=predator_probability,
                prey_density=prey_density,
                health=health,
                stamina=stamina,
                hunger=hunger,
                thirst=thirst,
            )
            try:
                thought_obj = json.loads(result["thought_log"])
            except json.JSONDecodeError:
                thought_obj = {"raw": result["thought_log"]}

            payload = {
                "species": species,
                "live_capture": bool(use_live),
                "inputs": {
                    "predator_probability": predator_probability,
                    "prey_density": prey_density,
                    "health": health,
                    "stamina": stamina,
                    "hunger": hunger,
                    "thirst": thirst,
                },
                "action": result["action"],
                "thought": thought_obj,
                "fast_facts": get_species_fast_facts(species),
            }
            if live_frame is not None:
                payload["capture"] = {
                    "frame_id": live_frame.frame_id,
                    "timestamp_ms": live_frame.timestamp_ms,
                    "region": list(live_frame.region),
                    "width": live_frame.width,
                    "height": live_frame.height,
                    "mean_brightness": live_frame.mean_brightness,
                    "motion_score": live_frame.motion_score,
                    "source": live_frame.source,
                    "error": live_frame.error,
                }
            self._send_json(payload)

    return CompanionRequestHandler


def main() -> None:
    parser = argparse.ArgumentParser(description="Local PALEO Companion HUD server.")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind address (default: 127.0.0.1).",
    )
    parser.add_argument("--port", type=int, default=8765, help="Port (default: 8765).")
    parser.add_argument(
        "--live-capture",
        action="store_true",
        help="Use real-time screen capture (mss) for /api/hud inputs.",
    )
    args = parser.parse_args()

    pages_dir = _ROOT / "pages"
    if not pages_dir.is_dir():
        raise SystemExit(f"Missing pages directory: {pages_dir}")

    handler = make_handler(_ROOT, pages_dir, live_capture=args.live_capture)
    httpd = HTTPServer((args.host, args.port), handler)
    print(f"Serving {pages_dir} at http://{args.host}:{args.port}/")
    print("Open Companion HUD: http://127.0.0.1:%s/companion-hud.html" % args.port)
    if args.live_capture:
        print("Live capture mode enabled: /api/hud uses real screen region metrics.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
