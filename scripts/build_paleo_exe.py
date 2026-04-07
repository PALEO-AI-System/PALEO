"""Build Windows PALEO executables with PyInstaller."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _build(name: str, script_name: str) -> None:
    target = ROOT / "scripts" / script_name
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name",
        name,
        str(target),
    ]
    print(f"Building {name}.exe ...")
    print(" ".join(cmd))
    subprocess.check_call(cmd, cwd=str(ROOT))


def main() -> None:
    p = argparse.ArgumentParser(description="Build PALEO Windows executables.")
    p.add_argument(
        "--target",
        choices=["live", "overlay", "both"],
        default="both",
        help="Which executable(s) to build.",
    )
    args = p.parse_args()

    if args.target in ("live", "both"):
        _build("PALEO", "run_paleo_live.py")
    if args.target in ("overlay", "both"):
        _build("PALEOOverlay", "run_paleo_overlay.py")
    print("Done: dist/PALEO.exe and/or dist/PALEOOverlay.exe")


if __name__ == "__main__":
    main()
