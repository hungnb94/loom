import tempfile
from pathlib import Path
import pytest
from loom.nodes.log import LogNode


@pytest.mark.asyncio
async def test_log_node_basic():
    with tempfile.TemporaryDirectory() as tmp:
        log_file = Path(tmp) / "test.log"
        node = LogNode(
            name="test",
            config={
                "message": "Hello from log node",
                "file": str(log_file),
            },
        )
        success, output, state = await node.run({})

        assert success is True
        assert "Logged to" in output
        assert log_file.exists()
        content = log_file.read_text()
        assert "Hello from log node" in content


@pytest.mark.asyncio
async def test_log_node_with_template():
    with tempfile.TemporaryDirectory() as tmp:
        log_file = Path(tmp) / "test.log"
        node = LogNode(
            name="test",
            config={
                "message": "User: {{username}}",
                "file": str(log_file),
            },
        )
        success, output, state = await node.run({"username": "Alice"})

        assert success is True
        content = log_file.read_text()
        assert "User: Alice" in content


@pytest.mark.asyncio
async def test_log_node_appends():
    with tempfile.TemporaryDirectory() as tmp:
        log_file = Path(tmp) / "test.log"
        node1 = LogNode(name="first", config={"message": "Line 1", "file": str(log_file)})
        node2 = LogNode(name="second", config={"message": "Line 2", "file": str(log_file)})

        await node1.run({})
        await node2.run({})

        content = log_file.read_text()
        lines = content.strip().split("\n")
        assert lines == ["Line 1", "Line 2"]
