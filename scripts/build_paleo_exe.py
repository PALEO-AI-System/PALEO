"""Build Windows PALEO.exe launcher with PyInstaller."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    target = ROOT / "scripts" / "run_paleo_live.py"
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name",
        "PALEO",
        str(target),
    ]
    print("Building PALEO.exe ...")
    print(" ".join(cmd))
    subprocess.check_call(cmd, cwd=str(ROOT))
    print("Done: dist/PALEO.exe")


if __name__ == "__main__":
    main()
