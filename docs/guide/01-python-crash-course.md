# Python Crash Course for Loom

This chapter teaches only the Python concepts you need to understand the Loom codebase. We assume you know JavaScript async/promises — we'll map Python concepts to those.

---

## 1. Variables & Types

Python is dynamically typed (like JavaScript), but we often add **type hints** (like TypeScript):

```python
# Without type hints (valid but not used in this project)
name = "Loom"
count = 42

# With type hints (used everywhere in Loom)
name: str = "Loom"
count: int = 42
enabled: bool = True
```

Key difference from JavaScript: Python uses `None` instead of `null`, and `True`/`False` are capitalized.

---

## 2. Functions

```python
def greet(name: str) -> str:
    return f"Hello, {name}"

# Call it
message = greet("World")
```

The `-> str` is a return type hint. It doesn't enforce anything at runtime — it's documentation for humans and type checkers.

**Default arguments:**

```python
def connect(host: str = "localhost", port: int = 8080) -> None:
    print(f"Connecting to {host}:{port}")
```

`None` in Python = `void` in TypeScript = "returns nothing".

---

## 3. Classes

```python
class Dog:
    def __init__(self, name: str) -> None:
        self.name = name

    def bark(self) -> str:
        return f"{self.name} says woof!"

# Create instance
my_dog = Dog("Buddy")
print(my_dog.bark())  # Buddy says woof!
```

`__init__` is the constructor. `self` is like `this` in JavaScript — it must be the first parameter of every method.

---

## 4. Dataclasses

A **dataclass** is a shortcut for creating classes that mainly hold data:

```python
from dataclasses import dataclass

@dataclass
class PipelineState:
    current_node: str
    visit_counts: dict[str, int]
    shared_state: dict

# Create instance
state = PipelineState(
    current_node="start",
    visit_counts={},
    shared_state={"requirement": "fix bug"}
)

# Access fields
print(state.current_node)  # "start"
```

The `@dataclass` decorator automatically generates:
- `__init__` (constructor)
- `__repr__` (string representation)
- `__eq__` (equality comparison)

This is used in `loom/state.py`.

---

## 5. Inheritance

```python
class BaseNode:
    def __init__(self, name: str, config: dict) -> None:
        self.name = name
        self.config = config

    async def run(self, state: dict) -> tuple[bool, str, dict]:
        raise NotImplementedError("Subclasses must override this")

class ShellNode(BaseNode):
    async def run(self, state: dict) -> tuple[bool, str, dict]:
        # ShellNode implements its own run()
        return True, "output", state
```

`ShellNode(BaseNode)` means "ShellNode extends BaseNode". It inherits `__init__` and `name`/`config`, but overrides `run()`.

This pattern is used for all node types in `loom/nodes/`.

---

## 6. Async/Await

If you know JavaScript promises, Python async is nearly identical:

| JavaScript | Python |
|---|---|
| `async function` | `async def` |
| `await` | `await` |
| `Promise` | `asyncio.Task` / coroutine |
| `new Promise((resolve) => ...)` | `asyncio.create_task(...)` |

```python
import asyncio

async def fetch_data() -> str:
    await asyncio.sleep(1)  # Like setTimeout, but non-blocking
    return "data"

async def main() -> None:
    result = await fetch_data()
    print(result)

# Run the async function
asyncio.run(main())
```

In Loom, `node.run()` is always `async def` because it might spawn subprocesses that take time.

---

## 7. Subprocess

```python
import asyncio

async def run_command() -> str:
    proc = await asyncio.create_subprocess_shell(
        "echo hello",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return stdout.decode()

output = asyncio.run(run_command())
print(output)  # "hello\n"
```

Key points:
- `asyncio.create_subprocess_shell` = spawn a shell process
- `stdout=asyncio.subprocess.PIPE` = capture output instead of printing to terminal
- `await proc.communicate()` = wait for process to finish, get output
- `proc.returncode` = exit code (0 = success, non-zero = failure)

This is the core of `AgentNode` and `ShellNode`.

---

## 8. Dictionaries

Python `dict` = JavaScript `Object` / `Map`:

```python
config = {
    "entry": "clarify",
    "steps": {
        "clarify": {"type": "agent", "agent": "claude"},
    }
}

# Access
print(config["entry"])           # "clarify"
print(config.get("steps"))       # {...}
print(config.get("missing", {}))  # {} (default if key missing)

# Check
if "entry" in config:
    print("Has entry")
```

---

## 9. Type Hints Deep Dive

Common type hints in Loom:

```python
from typing import Any

# Union type (str or None)
name: str | None = None

# Dictionary with string keys and any values
state: dict[str, Any] = {}

# Tuple with fixed types
result: tuple[bool, str, dict] = (True, "output", {})

# List
tools: list[str] = ["Read", "Glob", "Grep"]
```

`str | None` is Python 3.10+ syntax. In older Python you'd write `Optional[str]`.

---

## 10. Pathlib (File Paths)

```python
from pathlib import Path

# Create path object
path = Path("examples/pipeline.yaml")

# Check
print(path.exists())     # True/False
print(path.is_file())    # True/False

# Read
content = path.read_text(encoding="utf-8")

# Write
path.write_text("hello", encoding="utf-8")
```

`pathlib.Path` is the modern way to handle file paths in Python. It's used throughout Loom.

---

## 11. YAML Parsing

```python
import yaml

# Load
with open("pipeline.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# config is now a Python dict
print(config["entry"])  # "clarify"
```

`yaml.safe_load` converts YAML to Python dict/list/scalars. It's used in `loom/config.py`.

---

## 12. Jinja2 Templates

```python
from jinja2 import Template

template = Template("Hello, {{name}}!")
result = template.render(name="World")
print(result)  # "Hello, World!"
```

In Loom, agent prompts are Jinja2 templates. Variables like `{{requirement}}` are replaced from `shared_state`.

---

## Next Step

Go to `02-project-overview.md` to understand what Loom does and how it's structured.
