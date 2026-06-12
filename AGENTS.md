# AGENTS.md — Loom

> Graph-based AI agent pipeline orchestrator. Mixed AI + shell nodes, conditional edges, verify-fix loops.

## What This Project Does

Loom is a CLI tool that orchestrates AI agent pipelines defined as graphs. Each node is either an **agent node** (calls an AI CLI as a subprocess with streaming output) or a **shell node** (runs shell commands with exit-code routing). Edges are conditional — `on_pass` / `on_fail` — enabling verify-fix loops and multi-stage workflows like `clarify → plan → execute → verify → review → done`.

Key capabilities:
- **Agent-agnostic**: Supports `claude`, `opencode`, or any custom binary via `~/.loom/agents.yaml`.
- **Streaming TUI**: Live subprocess output streamed to a Rich terminal UI during 60-90s agent runs.
- **Durable execution**: Pipeline state is persisted to `pipeline.state` before each node for crash recovery.
- **Loop prevention**: `max_visits` per node prevents infinite cycles.

## Architecture

```
loom/
├── loom/
│   ├── cli.py          ← Entry point + Rich TUI
│   ├── executor.py     ← GraphExecutor: graph traversal, state management
│   ├── nodes/
│   │   ├── agent.py    ← AgentNode: subprocess spawn + streaming + verdict parsing
│   │   └── shell.py    ← ShellNode: sequential commands + exit code routing
│   ├── agents.py       ← AgentAdapter: load ~/.loom/agents.yaml, resolve binaries
│   ├── state.py        ← PipelineState dataclass: current_node, visit_counts, shared_state
│   └── config.py       ← Load pipeline.yaml, validate node types + edge references
├── examples/
│   ├── pipeline.yaml   ← Example: clarify → plan → execute → verify → review → done
│   └── agents.yaml     ← Example: claude + opencode registry
├── pyproject.toml
├── README.md
└── CONTEXT.md          ← Design decisions + V1 scope
```

## Key Technical Details

### Node Types

**Agent node** (`type: agent`):
- Spawns the configured AI CLI as a subprocess.
- Streams stdout/stderr live to the TUI.
- Parses a verdict keyword (e.g., `PASS` / `FAIL`) from the start of the output to decide routing.
- Prompts support Jinja2-style variable substitution from `shared_state` (e.g., `{{requirement}}`, `{{clarify_output}}`).

**Shell node** (`type: shell`):
- Runs a list of shell commands sequentially in the project directory.
- Routing is decided by the final exit code: `0` → `on_pass`, non-zero → `on_fail`.
- No LLM parsing — pure exit-code logic.

### State & Persistence

- `shared_state` is a Python dict passed between nodes. Each node's output is stored as `{node_name}_output`.
- `visit_counts` tracks how many times each node has been entered (enforces `max_visits`).
- Before every node execution, the full state is serialized to `pipeline.state` (JSON) for crash recovery.
- On restart, `GraphExecutor` reads `pipeline.state` and resumes from `current_node`.

### Configuration Files

- **`pipeline.yaml`** (project-local): Defines the graph — nodes, edges, prompts, tools, `max_visits`.
- **`~/.loom/agents.yaml`** (global): Agent registry — binary paths, default models, API key env vars. Machine-specific, not committed.

### Verdict Parsing

- Agent nodes specify a `pass_keyword` (default: `PASS`).
- The executor scans the first N lines of the agent's output for this keyword.
- If found → route `on_pass`; else → route `on_fail`.
- If `on_pass`/`on_fail` is omitted, the executor falls back to a default `next` edge.

## Dependencies & Environment

- Python 3.10+
- `rich` (TUI)
- `pyyaml` (config parsing)
- `jinja2` (prompt templating)
- External AI CLIs (`claude`, `opencode`, etc.) must be installed separately and referenced in `~/.loom/agents.yaml`.

## Common Tasks

| Task | Command / File |
|---|---|
| Run a pipeline | `loom run "requirement"` or `loom run` (interactive prompt) |
| Define a pipeline | Edit `pipeline.yaml` in the project root |
| Register an agent | Edit `~/.loom/agents.yaml` |
| Resume after crash | `loom run` — auto-detects `pipeline.state` and resumes |
| Add a new node type | Implement in `loom/nodes/`, register in `config.py` |

## Testing

- Unit tests for `GraphExecutor` state machine (mock nodes).
- Integration tests for agent subprocess spawning (use dummy binaries).
- TUI tests via Rich's `Console` capture.

## Design Decisions (from CONTEXT.md)

| Decision | Choice | Rationale |
|---|---|---|
| Agent invocation | Subprocess CLI | Agents need file tools (Read/Edit/Bash) — direct API lacks them |
| Pipeline config | Local `pipeline.yaml` | Pipelines are project-specific |
| Agent config | Global `~/.loom/agents.yaml` | API keys / binary paths are machine-specific |
| Agent support | Adapter pattern | Support `claude`, `opencode`, custom binaries |
| UI | Rich TUI + streaming | Users need live output during long agent runs |
| Business model | Open source core + cloud hosting | Validated model (n8n, Supabase) |

## V1 Scope

- `loom run ["requirement"]` — CLI entry point
- Read `pipeline.yaml` + `agents.yaml`
- Execute agent nodes (subprocess, stream to TUI)
- Execute shell nodes (exit code routing)
- Conditional edges (`on_pass` / `on_fail`)
- `max_visits` loop prevention
- `pipeline.state` durable execution + crash recovery
- Rich TUI (progress list + live streaming)

## Notes for AI Agents

- **Always read `pipeline.yaml` first** before modifying any node — edge references must stay consistent.
- **Never commit `~/.loom/agents.yaml`** — it contains API keys and machine-specific paths.
- **When adding a node**, ensure:
  1. The node has a unique name.
  2. All `on_pass` / `on_fail` / `next` edges point to existing nodes.
  3. `max_visits` is set if the node can loop back to itself.
- **When modifying state logic**, update `state.py` AND `executor.py` — the persistence layer must match the dataclass.
- **Agent prompts are Jinja2 templates** — variables come from `shared_state`. Undefined variables will raise at runtime.
