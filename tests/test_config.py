from pathlib import Path
from loom.config import load_pipeline, load_agents

def test_load_pipeline():
    config = load_pipeline(Path("examples/pipeline.yaml"))
    assert config["entry"] == "clarify"
    assert "steps" in config
    assert config["steps"]["clarify"]["type"] == "agent"

def test_load_agents():
    agents = load_agents(Path("examples/agents.yaml"))
    assert "claude" in agents
    assert agents["claude"]["binary"] == "claude"
