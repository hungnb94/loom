#!/usr/bin/env python3
"""Stop hook: blocks Claude from stopping mid-pipeline."""
import json
import re
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # hooks/ -> .claude/ -> project root
STATE_PATH = PROJECT_ROOT / ".pipeline/pipeline.state"


def render(template: str, state: dict) -> str:
    return re.sub(r"\{\{(\w+)\}\}", lambda m: str(state.get(m.group(1), m.group(0))), template)


def main():
    if not STATE_PATH.exists():
        sys.exit(0)

    try:
        state = json.loads(STATE_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        sys.exit(0)

    if state.get("mode") != "pipeline":
        sys.exit(0)

    pipeline_path = PROJECT_ROOT / state.get("pipeline", ".pipeline/pipeline.yaml")
    if not pipeline_path.exists():
        sys.exit(0)

    try:
        config = yaml.safe_load(pipeline_path.read_text())
    except Exception:
        sys.exit(0)

    current = state.get("current_step", "")
    step = config.get("steps", {}).get(current, {})

    if not step:
        sys.exit(0)

    if step.get("terminal"):
        sys.exit(0)

    shared = state.get("shared_state", {})
    shared["requirement"] = state.get("requirement", "")

    prompt = render(step.get("prompt", ""), shared)
    step_type = step.get("type", "agent")
    agent = step.get("agent", "claude")

    print(
        f"Pipeline active — current step: '{current}' (type={step_type}, agent={agent}).\n"
        f"Complete this step before stopping.\n\n"
        f"Step prompt:\n{prompt.strip()}"
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
