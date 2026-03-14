"""Print Letta tool schemas for PALEO."""

from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.letta_tools import get_letta_tool_specs


def main() -> None:
    specs = [spec.__dict__ for spec in get_letta_tool_specs()]
    print(json.dumps(specs, indent=2))


if __name__ == "__main__":
    main()
