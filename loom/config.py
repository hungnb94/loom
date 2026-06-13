from pathlib import Path
from jinja2 import Template, TemplateSyntaxError
import yaml

VALID_TYPES = {"agent", "shell", "human", "condition", "subflow", "log", "parallel"}


def load_pipeline(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    validate_pipeline(config)
    return config


def load_agents(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config.get("agents", {})


def validate_pipeline(config: dict) -> None:
    """Full pipeline validation. Collects ALL errors, raises once."""
    errors = []

    # ── Structure ──
    if not isinstance(config, dict):
        raise ValueError("pipeline config must be a dict")

    if "entry" not in config:
        errors.append("pipeline must have 'entry' node")
    if "steps" not in config:
        errors.append("pipeline must have 'steps' section")
        raise ValueError("; ".join(errors))
    if not isinstance(config["steps"], dict):
        errors.append("pipeline 'steps' must be a dict")
        raise ValueError("; ".join(errors))

    entry = config.get("entry")
    steps = config["steps"]
    all_nodes = set(steps.keys())

    # ── Entry exists in steps ──
    if entry and entry not in all_nodes:
        errors.append(f"entry node '{entry}' not found in steps")

    # ── Per-node checks ──
    for name, step in steps.items():
        if "type" not in step:
            errors.append(f"step '{name}' missing 'type'")
            continue

        node_type = step["type"]

        # Unknown type
        if node_type not in VALID_TYPES:
            errors.append(f"step '{name}': unknown node type '{node_type}'")
            continue

        # Edge references
        edge_keys = [
            "on_pass", "on_fail", "on_true", "on_false", "next",
            "on_complete", "on_error", "on_approve", "on_decline", "on_skip",
        ]
        for key in edge_keys:
            target = step.get(key)
            if target and target not in all_nodes:
                errors.append(f"step '{name}': {key}='{target}' references non-existent node")

        # Type-specific required fields
        if node_type == "shell":
            if "commands" not in step:
                errors.append(f"step '{name}' (shell): missing 'commands'")
        elif node_type == "agent":
            if "agent" not in step:
                errors.append(f"step '{name}' (agent): missing 'agent'")
            if "prompt" not in step:
                errors.append(f"step '{name}' (agent): missing 'prompt'")
        elif node_type == "condition":
            if "expression" not in step:
                errors.append(f"step '{name}' (condition): missing 'expression'")
            if "on_true" not in step and "on_false" not in step:
                errors.append(f"step '{name}' (condition): needs at least on_true or on_false")
        elif node_type == "log":
            if "message" not in step:
                errors.append(f"step '{name}' (log): missing 'message'")
        elif node_type == "parallel":
            if "branches" not in step:
                errors.append(f"step '{name}' (parallel): missing 'branches'")

        # Jinja2 syntax check on string/list fields
        for field_key, field_val in step.items():
            values_to_check = []
            if isinstance(field_val, str):
                values_to_check.append(field_val)
            elif isinstance(field_val, list):
                values_to_check.extend(v for v in field_val if isinstance(v, str))

            for val in values_to_check:
                if "{{" in val or "{%" in val:
                    try:
                        Template(val)
                    except TemplateSyntaxError as e:
                        errors.append(f"step '{name}': field '{field_key}' has invalid Jinja2: {e}")

    # ── Unreachable nodes (from entry) ──
    if entry and entry in all_nodes:
        reachable = set()
        queue = [entry]
        while queue:
            current = queue.pop()
            if current in reachable:
                continue
            reachable.add(current)
            step = steps.get(current, {})
            for key in ("on_pass", "on_fail", "on_true", "on_false", "next",
                        "on_complete", "on_error", "on_approve", "on_decline"):
                target = step.get(key)
                if target and target in all_nodes:
                    queue.append(target)
            # Parallel branches
            for branch in step.get("branches", []):
                branch_next = branch.get("next") or branch.get("on_pass")
                if branch_next and branch_next in all_nodes:
                    queue.append(branch_next)

        unreachable = all_nodes - reachable
        if unreachable:
            errors.append(f"unreachable nodes: {', '.join(sorted(unreachable))}")

    # ── Raise all errors at once ──
    if errors:
        raise ValueError("; ".join(errors))
