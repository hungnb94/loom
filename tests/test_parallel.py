import pytest
import asyncio
from loom.parallel import ParallelDispatcher
from loom.nodes.shell import ShellNode


@pytest.mark.asyncio
async def test_parallel_dispatcher():
    nodes = [
        ShellNode(name="a", config={"commands": ["sleep 0.1 && echo a"]}),
        ShellNode(name="b", config={"commands": ["sleep 0.1 && echo b"]}),
    ]
    dispatcher = ParallelDispatcher(max_workers=2)
    results = await dispatcher.run(nodes, {})
    assert len(results) == 2
    assert "a" in results["a"][1]
    assert "b" in results["b"][1]
