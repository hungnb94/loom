import pytest
from pathlib import Path
from loom.config import load_pipeline, load_agents, validate_pipeline

def test_load_pipeline():
    config = load_pipeline(Path("examples/pipeline.yaml"))
    assert config["entry"] == "clarify"
    assert "steps" in config
    assert config["steps"]["clarify"]["type"] == "agent"

def test_load_agents():
    agents = load_agents(Path("examples/agents.yaml"))
    assert "claude" in agents
    assert agents["claude"]["binary"] == "claude"

def test_validate_pipeline_missing_entry():
    with pytest.raises(ValueError, match="'entry' node"):
        validate_pipeline({"steps": {}})

def test_validate_pipeline_missing_steps():
    with pytest.raises(ValueError, match="'steps' section"):
        validate_pipeline({"entry": "a"})

def test_validate_pipeline_missing_step_type():
    with pytest.raises(ValueError, match="missing 'type'"):
        validate_pipeline({"entry": "a", "steps": {"a": {}}})
