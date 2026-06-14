# Tutorial: Adding a Log Node

This is the hands-on tutorial. You will add a new `log` node type to Loom, write tests for it, and run the full test suite.

By the end, you will understand:
- How to create a new node type
- How to register it in the system
- How to write tests
- How the node fits into the graph executor

---

## Step 0: Understand the Goal

A `log` node writes a message to a file. It's simple but demonstrates the full pattern:

```yaml
steps:
  log_start:
    type: log
    message: "Pipeline started at {{timestamp}}"
    file: "pipeline.log"
    next: clarify
```

The `{{timestamp}}` is a Jinja2 template variable that gets replaced from `shared_state`.

---

## Step 1: Create the Node File

Create `loom/nodes/log.py`:

```python
from pathlib import Path
from jinja2 import Template
from loom.nodes.base import BaseNode


class LogNode(BaseNode):
    """Write a log message to a file.

    Supports Jinja2 templating for message content.
    """

    async def run(self, state: dict) -> tuple[bool, str, dict]:
        message_template = self.config.get("message", "")
        file_path_str = self.config.get("file", "loom.log")

        # Render Jinja2 template with state variables
        template = Template(message_template)
        rendered_message = template.render(**state)

        # Write to file (append mode)
        file_path = Path(file_path_str)
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(rendered_message + "\n")

        return True, f"Logged to {file_path}", state
```

**What this does:**
1. Gets `message` and `file` from node config
2. Renders the message using Jinja2 (replaces `{{variable}}` with values from `state`)
3. Appends the rendered message to the file
4. Returns `(True, output, state)` — `True` means success

---

## Step 2: Register the Node

Open `loom/executor.py` and add `LogNode` to `NODE_REGISTRY`:

```python
from loom.nodes.log import LogNode  # Add this import at the top

NODE_REGISTRY = {
    "agent": AgentNode,
    "shell": ShellNode,
    "human": HumanNode,
    "condition": ConditionNode,
    "subflow": SubflowNode,
    "log": LogNode,  # Add this line
}
```

This tells `GraphExecutor` that when it sees `type: log` in pipeline.yaml, it should create a `LogNode` instance.

---

## Step 3: Write Tests

Create a test file `tests/test_log_node.py`:

```python
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
```

**What these tests check:**
1. `test_log_node_basic` — basic logging works, file is created
2. `test_log_node_with_template` — Jinja2 template variables are replaced
3. `test_log_node_appends` — multiple log calls append (don't overwrite)

---

## Step 4: Run Your Tests

```bash
pytest tests/test_log_node.py -v
```

Expected output:

```
tests/test_log_node.py::test_log_node_basic PASSED                     [ 33%]
tests/test_log_node.py::test_log_node_with_template PASSED              [ 66%]
tests/test_log_node.py::test_log_node_appends PASSED                    [100%]

============================== 3 passed in 0.1s ==============================
```

---

## Step 5: Run Full Test Suite

Make sure you didn't break anything:

```bash
pytest
```

All 28 tests should pass (25 original + 3 new).

---

## Step 6: Test in a Real Pipeline

Create a test pipeline file `test_pipeline.yaml`:

```yaml
entry: log_start

steps:
  log_start:
    type: log
    message: "Pipeline started for: {{requirement}}"
    file: "pipeline.log"
    next: done

  done:
    type: shell
    commands:
      - echo "Pipeline complete"
```

Run it:

```bash
loom --requirement "test feature" --pipeline test_pipeline.yaml
```

Check the log file:

```bash
cat pipeline.log
```

You should see:

```
Pipeline started for: test feature
```

---

## Step 7: Clean Up

Remove test files:

```bash
rm test_pipeline.yaml pipeline.log
```

---

## What You Learned

1. **Node pattern**: Every node extends `BaseNode`, implements `run()`, returns `(bool, str, dict)`
2. **Registration**: Add to `NODE_REGISTRY` in `executor.py`
3. **Templating**: Use Jinja2 to substitute variables from `shared_state`
4. **Testing**: Use `pytest.mark.asyncio`, `tempfile.TemporaryDirectory`, and `assert`
5. **Integration**: Test with a real pipeline YAML file and the `loom` CLI

---

## Next Step

Go to `05-reference.md` for a comprehensive reference of all node types, config formats, and APIs.
