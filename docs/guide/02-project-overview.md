# Project Overview

This chapter explains what Loom does, why it exists, and how the codebase is organized.

---

## What is Loom?

Loom is a **pipeline orchestrator**. It runs a series of steps (called "nodes") in a graph structure, where each step can be:

1. **An AI agent** — spawns an AI CLI (like Claude or OpenCode) as a subprocess, streams its output, and checks if it succeeded
2. **A shell command** — runs commands like `yarn build` or `pytest`, checks exit code
3. **A human checkpoint** — pauses and asks for approval
4. **A condition** — evaluates a Python expression to decide which path to take
5. **A subflow** — runs another pipeline inside the current one

The key feature is **conditional edges**: each node can route to different next nodes depending on success/failure. This enables **verify-fix loops**:

```
execute → verify → review
            ↑      │
            └──── fix_code (if verify or review fails)
```

If `verify` fails, it goes to `fix_code`, then back to `verify`. If it passes, it goes to `review`.

---

## Why Subprocess?

You might wonder: why not call AI APIs directly? Why spawn a subprocess?

Because AI agents need **file tools** — they need to read files, edit code, run shell commands. The Claude CLI (`claude`) and OpenCode CLI (`opencode`) have these tools built-in. Calling their API directly would not give you these capabilities.

So Loom's approach is: **orchestrate the orchestrators**. Loom manages the pipeline; the AI CLIs do the actual work.

---

## File Structure

```
loom/
├── loom/                      ← Main package
│   ├── __init__.py            ← Package version
│   ├── cli.py                 ← CLI entry point (Typer + Rich TUI)
│   ├── executor.py            ← GraphExecutor: traverses the graph
│   ├── state.py               ← PipelineState dataclass
│   ├── config.py              ← Load and validate pipeline.yaml
│   ├── agents.py              ← AgentAdapter: resolve agent binaries
│   ├── tui.py                 ← Rich terminal UI
│   ├── parallel.py            ← ParallelDispatcher (thread pool)
│   └── nodes/                 ← Node implementations
│       ├── __init__.py
│       ├── base.py            ← BaseNode abstract class
│       ├── agent.py           ← AgentNode (subprocess AI)
│       ├── shell.py           ← ShellNode (shell commands)
│       ├── human.py           ← HumanNode (approval checkpoint)
│       ├── condition.py       ← ConditionNode (expression evaluation)
│       └── subflow.py         ← SubflowNode (nested pipeline)
├── tests/                     ← Test suite
│   ├── test_executor.py       ← GraphExecutor tests
│   ├── test_nodes.py          ← Node type tests
│   ├── test_cli.py            ← CLI tests
│   ├── test_config.py         ← Config loading tests
│   ├── test_agents.py         ← Agent resolution tests
│   ├── test_state.py          ← State persistence tests
│   ├── test_tui.py            ← TUI tests
│   └── test_parallel.py       ← Parallel execution tests
├── examples/
│   ├── pipeline.yaml          ← Example pipeline
│   └── agents.yaml            ← Example agent registry
├── docs/
│   └── guide/                 ← This guide
├── pyproject.toml             ← Project config (dependencies, scripts)
├── README.md                  ← Quick start
├── AGENTS.md                  ← AI agent instructions
└── CONTEXT.md                 ← Design decisions
```

---

## Key Concepts

### Pipeline

A pipeline is defined in `pipeline.yaml`:

```yaml
entry: clarify

steps:
  clarify:
    type: agent
    agent: claude
    prompt: "..."
    on_pass: plan

  plan:
    type: agent
    agent: claude
    prompt: "..."
    next: execute
```

- `entry`: The first node to run
- `steps`: Dictionary of node configurations
- Each step has `type`, plus type-specific fields

### State

`PipelineState` is a dataclass that tracks:
- `current_node`: Which node is currently running
- `visit_counts`: How many times each node has been visited (loop prevention)
- `shared_state`: Dictionary passed between nodes, storing outputs

Before each node runs, the state is saved to `pipeline.state` (JSON file). If Loom crashes, you can resume with `loom --resume`.

### Node Types

| Type | Purpose | Routing |
|---|---|---|
| `agent` | Spawn AI CLI subprocess | `pass_keyword` in output → `on_pass`/`on_fail` |
| `shell` | Run shell commands | Exit code 0 → `on_pass`, non-zero → `on_fail` |
| `human` | Wait for human approval | `on_approve`/`on_decline` |
| `condition` | Evaluate expression | `on_true`/`on_false` |
| `subflow` | Run nested pipeline | `on_complete`/`on_error` |

### Routing

Every node has a `route(success: bool)` method that returns the next node name:

```python
def route(self, success: bool) -> str | None:
    if success:
        return self.config.get("on_pass") or self.config.get("next")
    else:
        return self.config.get("on_fail") or self.config.get("next")
```

If `route` returns `None`, the pipeline ends.

---

## Data Flow

```
1. CLI parses arguments
2. Load pipeline.yaml → config dict
3. Create GraphExecutor with config
4. Create PipelineState (or load from pipeline.state)
5. executor.run(state) starts the loop:
   a. Check max_visits
   b. Create node instance
   c. await node.run(state) → (success, output, updated_state)
   d. Save output to shared_state
   e. Persist state to pipeline.state
   f. node.route(success) → next node
   g. Repeat until next is None
6. Print final state
```

---

## Next Step

Go to `03-running-tests.md` to learn how to run the test suite and verify everything works.
