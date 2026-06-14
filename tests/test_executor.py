import pytest
from loom.executor import GraphExecutor
from loom.state import PipelineState

@pytest.mark.asyncio
async def test_executor_linear_pipeline():
    config = {
        "entry": "start",
        "steps": {
            "start": {"type": "shell", "commands": ["echo start"], "next": "end"},
            "end": {"type": "shell", "commands": ["echo end"]}
        }
    }
    executor = GraphExecutor(config)
    state = PipelineState(current_node="start", visit_counts={}, shared_state={})
    final_state = await executor.run(state)
    assert final_state.current_node == "end"
    assert final_state.visit_counts["start"] == 1
    assert final_state.visit_counts["end"] == 1

@pytest.mark.asyncio
async def test_executor_conditional_pass():
    config = {
        "entry": "check",
        "steps": {
            "check": {"type": "condition", "expression": "True", "on_true": "pass", "on_false": "fail"},
            "pass": {"type": "shell", "commands": ["echo pass"]},
            "fail": {"type": "shell", "commands": ["echo fail"]}
        }
    }
    executor = GraphExecutor(config)
    state = PipelineState(current_node="check", visit_counts={}, shared_state={})
    final_state = await executor.run(state)
    assert final_state.current_node == "pass"


@pytest.mark.asyncio
async def test_full_pipeline():
    """Integration test: agent → shell → shell through a full graph."""
    config = {
        "entry": "clarify",
        "steps": {
            "clarify": {
                "type": "agent",
                "agent": "echo",
                "prompt": "PASS: clarified",
                "pass_keyword": "PASS",
                "on_pass": "execute",
            },
            "execute": {
                "type": "shell",
                "commands": ["echo done"],
                "on_pass": "done",
            },
            "done": {
                "type": "shell",
                "commands": ["echo finished"],
            },
        }
    }
    executor = GraphExecutor(config)
    state = PipelineState(
        current_node="clarify",
        visit_counts={},
        shared_state={"requirement": "test"},
    )
    final_state = await executor.run(state)
    assert final_state.current_node == "done"
    assert "clarify_output" in final_state.shared_state
    assert "execute_output" in final_state.shared_state
