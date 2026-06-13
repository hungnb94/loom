import pytest
from loom.executor import GraphExecutor
from loom.state import PipelineState
from loom.config import load_pipeline
from pathlib import Path
import asyncio
import json


def _run_pipeline(node=None, state=None):
    """Helper: run test pipeline, return final shared_state."""
    config = load_pipeline(Path("test_full_pipeline.yaml"))
    executor = GraphExecutor(config)
    if state is None:
        state = PipelineState(current_node=config["entry"], visit_counts={}, shared_state={"requirement": "test"})
    final = asyncio.run(executor.run(state, quiet=True))
    return final.shared_state


class TestOutputRetrieval:
    """Test shared_state output retrieval patterns."""

    def test_output_keys_exist(self):
        state = _run_pipeline()
        # Every node should have output stored as {name}_output
        for name in ["setup", "check_env", "parallel_verify", "log_result"]:
            assert f"{name}_output" in state

    def test_output_is_string(self):
        state = _run_pipeline()
        for key, val in state.items():
            if key.endswith("_output"):
                assert isinstance(val, str), f"{key} should be string, got {type(val)}"

    def test_shell_output_content(self):
        state = _run_pipeline()
        assert "Loom Full Pipeline Test" in state["setup_output"]

    def test_condition_output_content(self):
        state = _run_pipeline()
        assert "True" in state["check_env_output"]

    def test_log_output_content(self):
        state = _run_pipeline()
        assert "Logged to" in state["log_result_output"]

    def test_specific_node_lookup(self):
        state = _run_pipeline()
        key = "setup_output"
        assert key in state
        assert len(state[key]) > 0

    def test_missing_node_returns_none(self):
        state = _run_pipeline()
        output = state.get("nonexistent_output")
        assert output is None

    def test_serializable_to_json(self):
        state = _run_pipeline()
        # shared_state should be JSON-serializable
        serialized = json.dumps(state)
        assert len(serialized) > 0
        parsed = json.loads(serialized)
        assert "setup_output" in parsed
