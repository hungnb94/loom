# Loom — Design Context

Graph-based AI agent pipeline orchestrator. Mixed AI + shell nodes, conditional edges, verify-fix loops.

## Architecture Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Agent invocation | Subprocess CLI | Agent needs file tools (Read/Edit/Bash) — direct API doesn't have them |
| Pipeline config | Local `pipeline.yaml` per project | Pipelines are project-specific |
| Agent config | Global `~/.loom/agents.yaml` | API keys/binary paths are machine-specific, not committed |
| Agent support | Agent-agnostic adapter | Support `claude`, `opencode`, custom binaries |
| UI | Rich TUI + streaming subprocess output | User needs live output during 60-90s agent runs |
| Business model | Open source core + cloud hosting | Validated model (n8n, Supabase) |

## V1 Scope

```
loom run "requirement"    — or interactive prompt if no arg
Read pipeline.yaml        — graph nodes + edges
Read agents.yaml          — agent registry
Execute agent nodes       — subprocess, stream output to TUI
Execute shell nodes       — exit code routing (yarn build/test/lint)
Conditional edges         — on_pass / on_fail per node
max_visits per node       — prevent infinite loops
pipeline.state            — durable execution, crash recovery
Rich TUI                  — progress list + live streaming
```

## Node Types

### Agent Node
Calls AI CLI as subprocess. Output streamed to TUI. Verdict parsed from keyword at output start.

```yaml
review:
  type: agent
  agent: claude
  tools: [Read, Glob, Grep]
  prompt: "Review code. Reply PASS or FAIL: [issues]"
  pass_keyword: PASS
  on_pass: done
  on_fail: fix_code
```

### Shell Node
Runs commands sequentially. Exit code decides routing — no LLM, no parsing.

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

## Typical Pipeline Shape

```
clarify → plan → execute → verify ←─────────┐
                               │ PASS        │ FAIL
                            review        fix_code
                               │ PASS        ↑
                              done       (also from review fail)
```

## Shared State

Passed between nodes as a Python dict. Each node's output stored as `{node_name}_output`.
Persisted to `pipeline.state` before each node runs for crash recovery.

```json
{
  "current_node": "verify",
  "visit_counts": { "verify": 2, "fix_code": 1 },
  "shared_state": {
    "requirement": "...",
    "clarify_output": "...",
    "verify_output": "FAILED: yarn test\nAssertionError..."
  }
}
```

## Project Structure (planned)

```
loom/
├── CONTEXT.md              ← this file
├── loom/
│   ├── __init__.py
│   ├── cli.py              ← entry point, Rich TUI
│   ├── executor.py         ← GraphExecutor
│   ├── nodes/
│   │   ├── agent.py        ← AgentNode: subprocess + streaming
│   │   └── shell.py        ← ShellNode: commands + exit code
│   ├── agents.py           ← AgentAdapter, load agents.yaml
│   ├── state.py            ← PipelineState dataclass
│   └── config.py           ← load pipeline.yaml
├── examples/
│   ├── pipeline.yaml       ← example pipeline
│   └── agents.yaml         ← example agent config
├── pyproject.toml
└── README.md
```
