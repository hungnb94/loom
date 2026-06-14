import pytest
from loom.nodes.parallel import ParallelNode
from loom.nodes.shell import ShellNode
from loom.executor import GraphExecutor
from loom.state import PipelineState


@pytest.mark.asyncio
async def test_parallel_node_all_pass():
    """Parallel node succeeds when all branches pass."""
    node = ParallelNode(
        name="parallel_test",
        config={
            "branches": [
                {"name": "a", "type": "shell", "commands": ["echo a"]},
                {"name": "b", "type": "shell", "commands": ["echo b"]},
            ],
            "on_pass": "next_step",
            "on_fail": "fix",
        },
    )
    success, output, state = await node.run({})
    assert success is True
    assert "a_output" in state
    assert "b_output" in state
    assert "a" in state["a_output"]
    assert "b" in state["b_output"]


@pytest.mark.asyncio
async def test_parallel_node_any_fail():
    """Parallel node fails when any branch fails."""
    node = ParallelNode(
        name="parallel_test",
        config={
            "branches": [
                {"name": "pass", "type": "shell", "commands": ["echo ok"]},
                {"name": "fail", "type": "shell", "commands": ["exit 1"]},
            ],
            "on_pass": "next_step",
            "on_fail": "fix",
        },
    )
    success, output, state = await node.run({})
    assert success is False
    assert "fail_output" in state or "pass_output" in state


@pytest.mark.asyncio
async def test_parallel_node_routes_on_pass():
    """Parallel node routes to on_pass when all branches succeed."""
    node = ParallelNode(
        name="parallel_test",
        config={
            "branches": [
                {"name": "x", "type": "shell", "commands": ["echo x"]},
            ],
            "on_pass": "done",
            "on_fail": "retry",
        },
    )
    assert node.route(True) == "done"
    assert node.route(False) == "retry"


@pytest.mark.asyncio
async def test_parallel_node_integration_in_executor():
    """Parallel node works inside GraphExecutor."""
    config = {
        "entry": "parallel",
        "steps": {
            "parallel": {
                "type": "parallel",
                "branches": [
                    {"name": "lint", "type": "shell", "commands": ["echo lint-ok"]},
                    {"name": "test", "type": "shell", "commands": ["echo test-ok"]},
                ],
                "on_pass": "done",
            },
            "done": {"type": "shell", "commands": ["echo finished"]},
        },
    }
    executor = GraphExecutor(config)
    state = PipelineState(current_node="parallel", visit_counts={}, shared_state={})
    final_state = await executor.run(state)
    assert final_state.current_node == "done"
    assert "lint_output" in final_state.shared_state
    assert "test_output" in final_state.shared_state
