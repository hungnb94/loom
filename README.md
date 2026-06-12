# Loom

Graph-based AI agent pipeline orchestrator. Mixed AI + shell nodes, conditional edges, verify-fix loops.

## Installation

```bash
pip install -e ".[dev]"
```

## Usage

```bash
# Interactive prompt
loom

# With requirement
loom --requirement "Fix login bug"

# Resume session
loom --resume

# Debug mode
loom --debug
```

## Configuration

- `pipeline.yaml` — project-local pipeline definition
- `~/.loom/agents.yaml` — global agent registry

## Example Pipeline

See `examples/pipeline.yaml` for a complete example.
