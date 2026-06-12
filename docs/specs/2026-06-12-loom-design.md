# Loom Design Spec

> Graph-based AI agent pipeline orchestrator. Mixed AI + shell nodes, conditional edges, verify-fix loops.
> Base: Học pattern từ Dagu (Go) + Prefect (Python), tự implement bằng Python với Typer + Rich.

## 1. Tổng quan

Loom là CLI tool orchestrate AI agent pipelines dưới dạng graph. Mỗi node là agent node (gọi AI CLI subprocess với streaming output) hoặc shell node (chạy shell commands với exit-code routing). Edges có điều kiện — `on_pass` / `on_fail` — cho phép verify-fix loops và multi-stage workflows.

### Key capabilities
- **Agent-agnostic**: Hỗ trợ `claude`, `opencode`, hoặc bất kỳ custom binary nào qua `~/.loom/agents.yaml`.
- **Streaming TUI**: Live subprocess output streamed tới Rich terminal UI trong khi agent chạy 60-90s.
- **Durable execution**: Pipeline state được persist tới `pipeline.state` trước mỗi node để crash recovery.
- **Loop prevention**: `max_visits` mỗi node ngăn infinite cycles.
- **Parallel execution**: Có thể chạy nhiều node song song nếu không phụ thuộc nhau.

## 2. Architecture

```
loom/
├── loom/
│   ├── __init__.py
│   ├── cli.py          ← Entry point + Rich TUI
│   ├── executor.py     ← GraphExecutor: graph traversal, state management
│   ├── nodes/
│   │   ├── agent.py    ← AgentNode: subprocess spawn + streaming + verdict parsing
│   │   ├── shell.py    ← ShellNode: sequential commands + exit code routing
│   │   ├── human.py    ← HumanNode: pause để user approve/decline
│   │   ├── condition.py← ConditionNode: if/else logic
│   │   └── subflow.py  ← SubflowNode: gọi pipeline khác
│   ├── agents.py       ← AgentAdapter: load ~/.loom/agents.yaml, resolve binaries
│   ├── state.py        ← PipelineState dataclass: current_node, visit_counts, shared_state
│   ├── config.py       ← Load pipeline.yaml, validate node types + edge references
│   ├── parallel.py     ← ParallelDispatcher: quản lý node song song
│   └── tui.py          ← Rich TUI: progress list + live streaming panels
├── examples/
│   ├── pipeline.yaml   ← Example: clarify → plan → execute → verify → review → done
│   └── agents.yaml     ← Example: claude + opencode registry
├── pyproject.toml
├── README.md
└── CONTEXT.md          ← Design decisions + V1 scope
```

## 3. Node Types

### 3.1 Agent Node (`type: agent`)
- Spawn AI CLI được cấu hình như subprocess.
- Stream stdout/stderr live tới TUI.
- Parse verdict keyword (e.g., `PASS` / `FAIL`) từ đầu output để quyết định routing.
- Prompts hỗ trợ Jinja2-style variable substitution từ `shared_state` (e.g., `{{requirement}}`, `{{clarify_output}}`).

### 3.2 Shell Node (`type: shell`)
- Chạy list shell commands sequentially trong project directory.
- Routing quyết định bởi final exit code: `0` → `on_pass`, non-zero → `on_fail`.
- Không có LLM parsing — pure exit-code logic.

### 3.3 Human Node (`type: human`) — NEW
- Pause pipeline, hiển thị prompt trong TUI.
- Chờ user input (approve/decline/skip) trước khi tiếp tục.
- Routing: `on_approve` / `on_decline` / `on_skip`.

### 3.4 Condition Node (`type: condition`) — NEW
- Đánh giá expression Jinja2 trên `shared_state`.
- Routing: `on_true` / `on_false`.
- Không spawn subprocess, không có side effects.

### 3.5 Subflow Node (`type: subflow`) — NEW
- Gọi một pipeline YAML khác như sub-workflow.
- Truyền `shared_state` xuống, nhận output trở lại.
- Hỗ trợ `on_complete` / `on_error` routing.

## 4. State & Persistence

- `shared_state` là Python dict truyền giữa các nodes. Mỗi node output được lưu là `{node_name}_output`.
- `visit_counts` theo dõi số lần mỗi node được enter (enforce `max_visits`).
- Trước mỗi node execution, full state được serialize tới `pipeline.state` (JSON) cho crash recovery.
- Khi restart, `GraphExecutor` đọc `pipeline.state` và resume từ `current_node`.

## 5. Parallel Execution

- Mặc định sequential. Node có thể cấu hình `parallel: true` để chạy song song với các node khác không phụ thuộc.
- `ParallelDispatcher` quản lý thread pool, đảm bảo dependency graph được tôn trọng.
- Shared state được merge sau khi tất cả parallel nodes hoàn thành.

## 6. Configuration Files

### 6.1 `pipeline.yaml` (project-local)
Định nghĩa graph — nodes, edges, prompts, tools, `max_visits`, `parallel`.

### 6.2 `~/.loom/agents.yaml` (global)
Agent registry — binary paths, default models, API key env vars. Machine-specific, không commit.

## 7. Verdict Parsing

- Agent nodes chỉ định `pass_keyword` (default: `PASS`).
- Executor scan N dòng đầu tiên của agent output cho keyword này.
- Nếu tìm thấy → route `on_pass`; ngược lại → route `on_fail`.
- Nếu `on_pass`/`on_fail` bị bỏ qua, executor fallback tới default `next` edge.

## 8. TUI (Rich)

- **Progress Panel**: Danh sách nodes với status (pending/running/completed/failed).
- **Streaming Panel**: Live output từ agent subprocess.
- **State Panel**: Hiển thị `shared_state` hiện tại (debug mode).
- **Human Input Panel**: Prompt cho human-in-the-loop nodes.

## 9. Dependencies & Environment

- Python 3.10+
- `typer` (CLI framework)
- `rich` (TUI)
- `pyyaml` (config parsing)
- `jinja2` (prompt templating)
- `asyncio` (parallel execution)
- External AI CLIs (`claude`, `opencode`, etc.) phải được cài riêng và reference trong `~/.loom/agents.yaml`.

## 10. Common Tasks

| Task | Command / File |
|---|---|
| Run a pipeline | `loom` (interactive prompt) hoặc `loom --requirement "..."` |
| Resume session cũ | `loom --resume` — đọc `pipeline.state` và tiếp tục từ node hiện tại |
| Define a pipeline | Edit `pipeline.yaml` trong project root |
| Register an agent | Edit `~/.loom/agents.yaml` |
| Add a new node type | Implement trong `loom/nodes/`, register trong `config.py` |
| Debug mode | `loom --debug` — hiển thị state panel |

## 11. Testing

- Unit tests cho `GraphExecutor` state machine (mock nodes).
- Integration tests cho agent subprocess spawning (use dummy binaries).
- TUI tests via Rich's `Console` capture.
- Parallel execution tests với mock slow nodes.

## 12. Design Decisions (from CONTEXT.md)

| Decision | Choice | Rationale |
|---|---|---|
| Agent invocation | Subprocess CLI | Agents cần file tools (Read/Edit/Bash) — direct API không có |
| Pipeline config | Local `pipeline.yaml` | Pipelines là project-specific |
| Agent config | Global `~/.loom/agents.yaml` | API keys / binary paths là machine-specific |
| Agent support | Adapter pattern | Hỗ trợ `claude`, `opencode`, custom binaries |
| UI | Rich TUI + streaming | Users cần live output trong khi agent chạy |
| Business model | Open source core + cloud hosting | Validated model (n8n, Supabase) |
| Base projects | Dagu + Prefect | Học pattern: YAML schema, state machine, parallel execution |

## 13. V1 Scope

- `loom` (interactive prompt) hoặc `loom --requirement "..."` — CLI entry point
- `loom --resume` — resume từ `pipeline.state`
- Read `pipeline.yaml` + `agents.yaml`
- Execute agent nodes (subprocess, stream to TUI)
- Execute shell nodes (exit code routing)
- Conditional edges (`on_pass` / `on_fail`)
- `max_visits` loop prevention
- `pipeline.state` durable execution + crash recovery
- Rich TUI (progress list + live streaming)
- Human-in-the-loop nodes
- Condition nodes
- Subflow nodes
- Parallel execution (basic)

## 14. Notes for AI Agents

- **Luôn đọc `pipeline.yaml` trước** trước khi modify bất kỳ node nào — edge references phải consistent.
- **Không bao giờ commit `~/.loom/agents.yaml`** — chứa API keys và machine-specific paths.
- **Khi thêm node**, đảm bảo:
  1. Node có unique name.
  2. Tất cả `on_pass` / `on_fail` / `next` edges trỏ tới existing nodes.
  3. `max_visits` được set nếu node có thể loop back.
- **Khi modify state logic**, update `state.py` VÀ `executor.py` — persistence layer phải match dataclass.
- **Agent prompts là Jinja2 templates** — variables từ `shared_state`. Undefined variables sẽ raise at runtime.
