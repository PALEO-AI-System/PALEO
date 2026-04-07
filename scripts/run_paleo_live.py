"""Launch Companion HUD server with optional live screen capture."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    p = argparse.ArgumentParser(description="Run PALEO companion HUD locally.")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument(
        "--no-live-capture",
        action="store_true",
        help="Disable live mss capture and use slider/manual HUD inputs only.",
    )
    p.add_argument(
        "--window-capture",
        action="store_true",
        help="Use configured fixed capture region (default is full primary monitor).",
    )
    p.add_argument(
        "--no-open-browser",
        action="store_true",
        help="Do not auto-open the HUD URL.",
    )
    args = p.parse_args()

    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "serve_companion.py"),
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    if not args.no_live_capture:
        cmd.append("--live-capture")
        if not args.window_capture:
            cmd.append("--full-screen")

    url = f"http://{args.host}:{args.port}/companion-hud.html"
    print(f"Starting PALEO HUD server: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, cwd=str(PROJECT_ROOT))
    try:
        if not args.no_open_browser:
            time.sleep(1.0)
            webbrowser.open(url)
            print(f"Opened {url}")
        proc.wait()
    except KeyboardInterrupt:
        print("\nStopping...")
        proc.terminate()
        proc.wait(timeout=5)


if __name__ == "__main__":
    main()
