import pytest
from loom.nodes.base import BaseNode
from loom.nodes.shell import ShellNode
from loom.nodes.agent import AgentNode
from loom.nodes.condition import ConditionNode
from loom.nodes.subflow import SubflowNode
from loom.nodes.log import LogNode
from loom.nodes.parallel import ParallelNode
from loom.executor import GraphExecutor, NODE_REGISTRY
from loom.state import PipelineState


def test_node_registry_has_all_types():
    """All node types must be registered in executor."""
    expected = {"agent", "shell", "condition", "subflow", "log", "parallel"}
    assert set(NODE_REGISTRY.keys()) == expected


def test_base_node_default_routing():
    """BaseNode.route uses on_pass/on_fail/next by default."""
    node = BaseNode(name="test", config={
        "on_pass": "success_node",
        "on_fail": "fail_node",
        "next": "fallback",
    })
    assert node.route(True) == "success_node"
    assert node.route(False) == "fail_node"


def test_base_node_default_routing_fallback():
    """BaseNode.route falls back to 'next' if on_pass/on_fail missing."""
    node = BaseNode(name="test", config={"next": "fallback"})
    assert node.route(True) == "fallback"
    assert node.route(False) == "fallback"


@pytest.mark.asyncio
async def test_shell_node_uses_jinja2_helper():
    """ShellNode renders commands with Jinja2."""
    node = ShellNode(name="test", config={"commands": ["echo {{name}}"]})
    success, output, state = await node.run({"name": "loom"})
    assert success is True
    assert "loom" in output


@pytest.mark.asyncio
async def test_agent_node_uses_jinja2_helper():
    """AgentNode renders prompt with Jinja2."""
    node = AgentNode(name="test", config={
        "agent": "echo",
        "prompt": "Hello {{name}}",
        "pass_keyword": "Hello",
    })
    success, output, state = await node.run({"name": "loom"})
    assert success is True
    assert "Hello loom" in output


@pytest.mark.asyncio
async def test_log_node_uses_jinja2_helper():
    """LogNode renders message with Jinja2."""
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as tmp:
        log_file = Path(tmp) / "test.log"
        node = LogNode(name="test", config={
            "message": "User: {{name}}",
            "file": str(log_file),
        })
        success, output, state = await node.run({"name": "Alice"})
        assert success is True
        content = log_file.read_text()
        assert "User: Alice" in content


@pytest.mark.asyncio
async def test_condition_node_uses_jinja2_helper():
    """ConditionNode renders expression with Jinja2."""
    node = ConditionNode(name="test", config={
        "expression": "{{x}} > 5",
        "on_true": "yes",
        "on_false": "no",
    })
    success, output, state = await node.run({"x": 10})
    assert success is True
    assert node.route(success) == "yes"


@pytest.mark.asyncio
async def test_parallel_node_uses_registry():
    """ParallelNode uses NODE_REGISTRY instead of hardcoded map."""
    node = ParallelNode(name="test", config={
        "branches": [
            {"name": "a", "type": "shell", "commands": ["echo a"]},
            {"name": "b", "type": "shell", "commands": ["echo b"]},
        ],
    })
    success, output, state = await node.run({})
    assert success is True
    assert "a_output" in state
    assert "b_output" in state


@pytest.mark.asyncio
async def test_executor_extracted_methods():
    """GraphExecutor methods are extractable and testable."""
    config = {
        "entry": "start",
        "steps": {
            "start": {"type": "shell", "commands": ["echo start"], "next": "end"},
            "end": {"type": "shell", "commands": ["echo end"]},
        }
    }
    executor = GraphExecutor(config)
    state = PipelineState(current_node="start", visit_counts={}, shared_state={})
    
    # _create_node should work
    node = executor._create_node("start")
    assert isinstance(node, ShellNode)
    
    # _check_max_visits should work
    executor._check_max_visits("start", {})  # no limit → no error
    executor._check_max_visits("start", {"start": 5})  # no limit → no error
    
    # Full run still works
    final_state = await executor.run(state, quiet=True)
    assert final_state.current_node == "end"
