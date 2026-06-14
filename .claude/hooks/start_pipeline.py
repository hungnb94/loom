#!/usr/bin/env python3
"""Start hook: resets pipeline mode to free at session start."""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # hooks/ -> .claude/ -> project root
STATE_PATH = PROJECT_ROOT / ".pipeline/pipeline.state"


def main():
    if not STATE_PATH.exists():
        sys.exit(0)
    try:
        state = json.loads(STATE_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        sys.exit(0)
    if state.get("mode") == "pipeline":
        state["mode"] = "free"
        STATE_PATH.write_text(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
