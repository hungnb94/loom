from pathlib import Path
import pytest
from loom.agents import AgentAdapter

def test_resolve_agent_binary():
    adapter = AgentAdapter(Path("examples/agents.yaml"))
    cmd = adapter.resolve("claude", "test prompt")
    assert cmd[0] == "claude"
    assert "--prompt" in cmd
    assert "test prompt" in cmd

def test_agent_not_found():
    adapter = AgentAdapter(Path("examples/agents.yaml"))
    with pytest.raises(ValueError):
        adapter.resolve("nonexistent", "test")
