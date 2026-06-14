# Running Tests

This chapter teaches you how to run the Loom test suite, understand test output, and use VS Code's test explorer.

---

## 1. Test Framework

Loom uses **pytest** — the most popular Python testing framework. It's similar to Jest in JavaScript:

| Jest | pytest |
|---|---|
| `test('name', () => { ... })` | `def test_name(): ...` |
| `expect(x).toBe(y)` | `assert x == y` |
| `async` tests with `async/await` | `@pytest.mark.asyncio` decorator |

---

## 2. Run All Tests

Make sure your virtual environment is activated:

```bash
source .venv/bin/activate
```

Run all tests:

```bash
pytest
```

You should see output like:

```
============================= test session starts ==============================
platform darwin -- Python 3.12.0, pytest-8.0.0, pluggy-1.0.0
rootdir: /Users/hung/Documents/Code/Python/loom
configfile: pyproject.toml
collected 25 items

tests/test_executor.py ...                                               [ 12%]
tests/test_nodes.py ..............                                       [ 68%]
tests/test_cli.py .                                                      [ 72%]
tests/test_config.py ....                                                [ 88%]
tests/test_agents.py ..                                                  [ 96%]
tests/test_state.py .                                                    [100%]
tests/test_tui.py ....                                                   [100%]
tests/test_parallel.py .                                                 [100%]

============================== 25 passed in 0.5s ==============================
```

Each `.` is a passing test. If you see `F`, that test failed. If you see `E`, there was an error.

---

## 3. Run Specific Test File

```bash
pytest tests/test_nodes.py
```

---

## 4. Run Specific Test

```bash
pytest tests/test_nodes.py::test_shell_node_success
```

---

## 5. Verbose Mode

```bash
pytest -v
```

Shows full test names and more detail:

```
tests/test_nodes.py::test_base_node_routing PASSED                    [  4%]
tests/test_nodes.py::test_shell_node_success PASSED                     [  8%]
tests/test_nodes.py::test_shell_node_failure PASSED                     [ 12%]
...
```

---

## 6. Stop on First Failure

```bash
pytest -x
```

Useful when debugging — stops immediately so you can fix the first failure before running the rest.

---

## 7. Run with Debug Output

```bash
pytest -s
```

Shows `print()` statements from tests (normally hidden).

---

## 8. VS Code Test Explorer

1. Open VS Code
2. Click the Testing icon in the left sidebar (beaker icon)
3. Click "Configure Python Tests"
4. Select "pytest"
5. Select "tests" folder

VS Code will discover all tests and show them in a tree. You can:
- Click the play button next to a test to run it
- Click the debug button to step through it
- See green checkmarks / red X for pass/fail

---

## 9. Understanding Test Structure

Let's look at a real test from `tests/test_nodes.py`:

```python
import pytest
from loom.nodes.shell import ShellNode

@pytest.mark.asyncio
async def test_shell_node_success():
    node = ShellNode(name="test", config={"commands": ["echo hello"], "on_pass": "done"})
    success, output, state = await node.run({})
    assert success is True
    assert "hello" in output
```

Breakdown:
- `import pytest` — brings in pytest decorators
- `from loom.nodes.shell import ShellNode` — imports the class being tested
- `@pytest.mark.asyncio` — tells pytest this is an async test
- `async def test_shell_node_success()` — async test function (must start with `test_`)
- `node = ShellNode(...)` — create the object under test
- `success, output, state = await node.run({})` — call the method, wait for result
- `assert success is True` — verify the result
- `assert "hello" in output` — verify output contains expected text

---

## 10. Mocking in Tests

Some tests use a simple mock pattern — creating an anonymous subclass:

```python
from loom.nodes.base import BaseNode

# Create a mock node that always succeeds
class MockNode(BaseNode):
    async def run(self, state):
        return True, "mock output", state

node = MockNode(name="mock", config={"next": "end"})
```

This is used in `test_executor.py` to test GraphExecutor without needing real AI agents.

---

## 11. Common pytest Options

| Option | Description |
|---|---|
| `pytest` | Run all tests |
| `pytest -v` | Verbose output |
| `pytest -x` | Stop on first failure |
| `pytest -s` | Show print statements |
| `pytest -k "shell"` | Run tests with "shell" in name |
| `pytest --tb=short` | Shorter traceback |
| `pytest --tb=long` | Full traceback |
| `pytest --pdb` | Drop into debugger on failure |

---

## 12. Test Configuration

Test settings are in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

This tells pytest-asyncio to automatically handle async tests without needing explicit event loop setup.

---

## Next Step

Go to `04-tutorial-log-node.md` for the hands-on tutorial: adding a new `log` node type from scratch.
