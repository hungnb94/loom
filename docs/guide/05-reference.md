# Reference

Comprehensive reference for Loom's architecture, node types, configuration, and APIs.

---

## Node Types

### BaseNode

Abstract base class for all nodes. Located in `loom/nodes/base.py`.

```python
class BaseNode:
    def __init__(self, name: str, config: dict) -> None:
        self.name = name
        self.config = config

    async def run(self, state: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        """Return (success, output, updated_state)."""
        raise NotImplementedError

    def route(self, success: bool) -> str | None:
        """Return next node name, or None to end pipeline."""
        if success:
            return self.config.get("on_pass") or self.config.get("next")
        else:
            return self.config.get("on_fail") or self.config.get("next")
```

### AgentNode

Spawns an AI CLI subprocess. Located in `loom/nodes/agent.py`.

**Config fields:**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `type` | str | Yes | — | Must be `"agent"` |
| `agent` | str | Yes | `"echo"` | Binary name (from `agents.yaml`) |
| `prompt` | str | Yes | `""` | Prompt text (Jinja2 template) |
| `pass_keyword` | str | No | `"PASS"` | Keyword to search for in output |
| `on_pass` | str | No | — | Next node if keyword found |
| `on_fail` | str | No | — | Next node if keyword not found |
| `next` | str | No | — | Fallback next node |
| `max_visits` | int | No | — | Loop prevention limit |

**Example:**

```yaml
review:
  type: agent
  agent: claude
  prompt: "Review code. Reply PASS or FAIL: [issues]"
  pass_keyword: PASS
  on_pass: done
  on_fail: fix_code
```

### ShellNode

Runs shell commands sequentially. Located in `loom/nodes/shell.py`.

**Config fields:**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `type` | str | Yes | — | Must be `"shell"` |
| `commands` | list[str] | Yes | `[]` | Commands to run |
| `on_pass` | str | No | — | Next node if all commands succeed |
| `on_fail` | str | No | — | Next node if any command fails |
| `next` | str | No | — | Fallback next node |
| `max_visits` | int | No | — | Loop prevention limit |

**Example:**

```yaml
verify:
  type: shell
  commands:
    - yarn build
    - yarn test --ci
    - yarn lint
  on_pass: review
  on_fail: fix_code
  max_visits: 5
```

### HumanNode

Pauses for human approval. Located in `loom/nodes/human.py`.

**Config fields:**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `type` | str | Yes | — | Must be `"human"` |
| `prompt` | str | No | — | Question to display |
| `on_approve` | str | No | — | Next node if approved |
| `on_decline` | str | No | — | Next node if declined |
| `on_skip` | str | No | — | Next node if skipped |
| `next` | str | No | — | Fallback next node |

**Example:**

```yaml
approve_deploy:
  type: human
  prompt: "Deploy to production?"
  on_approve: deploy
  on_decline: done
```

### ConditionNode

Evaluates a Jinja2-rendered Python expression. Located in `loom/nodes/condition.py`.

**Config fields:**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `type` | str | Yes | — | Must be `"condition"` |
| `expression` | str | Yes | `""` | Python expression (Jinja2 template) |
| `on_true` | str | No | — | Next node if expression is true |
| `on_false` | str | No | — | Next node if expression is false |
| `next` | str | No | — | Fallback next node |

**Example:**

```yaml
check_score:
  type: condition
  expression: "{{score}} > 80"
  on_true: pass
  on_false: retry
```

### SubflowNode

Runs a nested pipeline. Currently a stub (returns success immediately). Located in `loom/nodes/subflow.py`.

**Config fields:**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `type` | str | Yes | — | Must be `"subflow"` |
| `pipeline` | str | Yes | — | Path to sub-pipeline YAML |
| `on_complete` | str | No | — | Next node on success |
| `on_error` | str | No | — | Next node on failure |
| `next` | str | No | — | Fallback next node |

### LogNode (from Tutorial)

Writes a message to a file. Located in `loom/nodes/log.py`.

**Config fields:**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `type` | str | Yes | — | Must be `"log"` |
| `message` | str | Yes | `""` | Message to log (Jinja2 template) |
| `file` | str | No | `"loom.log"` | Log file path |
| `next` | str | No | — | Next node |

---

## Pipeline Configuration

### pipeline.yaml

```yaml
entry: <start_node_name>

steps:
  <node_name>:
    type: <node_type>
    # type-specific fields...
    on_pass: <next_node>
    on_fail: <other_node>
    max_visits: <number>
```

**Rules:**
- `entry` must be a key in `steps`
- Every step must have `type`
- `on_pass`/`on_fail`/`next` must reference existing nodes (or be omitted)
- `max_visits` prevents infinite loops

### agents.yaml

Located at `~/.loom/agents.yaml` (global, not committed):

```yaml
agents:
  <agent_name>:
    binary: <command_name>
    default_model: <model_name>
    api_key_env: <ENV_VAR_NAME>
```

**Example:**

```yaml
agents:
  claude:
    binary: claude
    default_model: claude-sonnet-4-6
    api_key_env: ANTHROPIC_API_KEY

  opencode:
    binary: opencode
    default_model: openrouter/deepseek/deepseek-chat-v3-1
    api_key_env: OPENROUTER_API_KEY
```

---

## State Format

### PipelineState

```python
@dataclass
class PipelineState:
    current_node: str
    visit_counts: dict[str, int]
    shared_state: dict[str, Any]
```

### pipeline.state (JSON file)

```json
{
  "current_node": "verify",
  "visit_counts": {
    "verify": 2,
    "fix_code": 1
  },
  "shared_state": {
    "requirement": "fix login bug",
    "clarify_output": "PASS: clarified requirement",
    "verify_output": "FAILED: yarn test\nAssertionError..."
  }
}
```

**Naming convention:** Each node's output is stored as `{node_name}_output` in `shared_state`.

---

## CLI Commands

```bash
# Interactive prompt
loom

# With requirement
loom --requirement "Fix login bug"
loom -r "Fix login bug"

# Specify pipeline file
loom --pipeline custom.yaml
loom -p custom.yaml

# Resume from crash
loom --resume

# Show debug state panel
loom --debug
```

---

## GraphExecutor API

```python
from loom.executor import GraphExecutor
from loom.state import PipelineState
from loom.config import load_pipeline
from pathlib import Path

# Load config
config = load_pipeline(Path("pipeline.yaml"))

# Create executor
executor = GraphExecutor(config)

# Create initial state
state = PipelineState(
    current_node=config["entry"],
    visit_counts={},
    shared_state={"requirement": "test"},
)

# Run (async)
import asyncio
final_state = asyncio.run(executor.run(state))
```

---

## TUI Components

### LoomTUI

Located in `loom/tui.py`.

```python
from loom.tui import LoomTUI
from rich.console import Console

console = Console()
tui = LoomTUI(console=console)

# Update node status
tui.update_node_status("clarify", "running")
tui.update_node_status("verify", "completed")
tui.update_node_status("fix_code", "failed")

# Update streaming output
tui.update_streaming("clarify", "Processing files...")

# Update state panel
tui.update_state({"current_step": 3, "total": 5})

# Render
panel = tui.render()
```

**Status values:** `pending`, `running`, `completed`, `failed`

---

## Next Step

Go to `06-troubleshooting.md` for common errors and debugging tips.
