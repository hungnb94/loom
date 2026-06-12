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
