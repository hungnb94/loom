import pytest
from loom.nodes.base import BaseNode


def test_base_node_routing():
    node = BaseNode(name="test", config={"on_pass": "next", "on_fail": "retry"})
    assert node.route(True) == "next"
    assert node.route(False) == "retry"


@pytest.mark.asyncio
async def test_shell_node_success():
    from loom.nodes.shell import ShellNode
    node = ShellNode(name="test", config={"commands": ["echo hello"], "on_pass": "done"})
    success, output, state = await node.run({})
    assert success is True
    assert "hello" in output


@pytest.mark.asyncio
async def test_shell_node_failure():
    from loom.nodes.shell import ShellNode
    node = ShellNode(name="test", config={"commands": ["exit 1"], "on_fail": "retry"})
    success, output, state = await node.run({})
    assert success is False


@pytest.mark.asyncio
async def test_shell_node_jinja2_template():
    """ShellNode should render Jinja2 templates in commands."""
    from loom.nodes.shell import ShellNode
    node = ShellNode(
        name="test",
        config={"commands": ["echo {{message}}"], "on_pass": "done"},
    )
    success, output, state = await node.run({"message": "hello world"})
    assert success is True
    assert "hello world" in output


@pytest.mark.asyncio
async def test_agent_node_pass():
    from loom.nodes.agent import AgentNode

    node = AgentNode(
        name="test",
        config={
            "agent": "echo",
            "prompt": "PASS: hello",
            "pass_keyword": "PASS",
            "on_pass": "done",
        },
    )
    success, output, state = await node.run({})
    assert success is True
    assert "PASS" in output


@pytest.mark.asyncio
async def test_agent_node_fail():
    from loom.nodes.agent import AgentNode

    node = AgentNode(
        name="test",
        config={
            "agent": "echo",
            "prompt": "FAIL: error",
            "pass_keyword": "PASS",
            "on_fail": "retry",
        },
    )
    success, output, state = await node.run({})
    assert success is False


@pytest.mark.asyncio
async def test_agent_node_jinja2_template():
    """AgentNode should render Jinja2 templates in prompts."""
    from loom.nodes.agent import AgentNode

    node = AgentNode(
        name="test",
        config={
            "agent": "echo",
            "prompt": "Requirement: {{requirement}} - PASS",
            "pass_keyword": "PASS",
            "on_pass": "done",
        },
    )
    success, output, state = await node.run({"requirement": "fix bug"})
    assert success is True
    assert "fix bug" in output
    assert "Requirement: fix bug" in output


@pytest.mark.asyncio
async def test_condition_node_true():
    from loom.nodes.condition import ConditionNode

    node = ConditionNode(
        name="test",
        config={
            "expression": "{{x}} > 5",
            "on_true": "yes",
            "on_false": "no",
        },
    )
    success, output, state = await node.run({"x": 10})
    assert success is True


@pytest.mark.asyncio
async def test_condition_node_false():
    from loom.nodes.condition import ConditionNode

    node = ConditionNode(
        name="test",
        config={
            "expression": "{{x}} > 5",
            "on_true": "yes",
            "on_false": "no",
        },
    )
    success, output, state = await node.run({"x": 3})
    assert success is False


@pytest.mark.asyncio
async def test_subflow_node():
    from loom.nodes.subflow import SubflowNode

    node = SubflowNode(
        name="test",
        config={
            "pipeline": "sub_pipeline.yaml",
            "on_complete": "next_step",
            "on_error": "retry",
        },
    )
    success, output, state = await node.run({})
    assert success is True
    assert "sub_pipeline.yaml" in output


@pytest.mark.asyncio
async def test_subflow_node_no_pipeline():
    from loom.nodes.subflow import SubflowNode

    node = SubflowNode(
        name="test",
        config={"on_complete": "next_step", "on_error": "retry"},
    )
    success, output, state = await node.run({})
    assert success is False
