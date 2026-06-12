from pathlib import Path
import yaml

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
    if "entry" not in config:
        raise ValueError("pipeline.yaml must have 'entry' node")
    if "steps" not in config:
        raise ValueError("pipeline.yaml must have 'steps' section")
    for name, step in config["steps"].items():
        if "type" not in step:
            raise ValueError(f"Step '{name}' must have 'type'")
