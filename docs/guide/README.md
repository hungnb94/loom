# Loom Developer Guide

A step-by-step guide for contributing to Loom, starting from zero Python knowledge.

## Who This Guide Is For

- **You** — coming back to the project after a break and need a refresher
- **New contributors** — who want to understand the codebase and add features
- **Anyone** — who knows terminal, Git, JSON, and async concepts but is new to Python

## Guide Structure

| File | Content | Purpose |
|---|---|---|
| `00-prerequisites.md` | Install Python, VS Code, Git, venv/uv | Setup your environment |
| `01-python-crash-course.md` | def, class, dataclass, async/await, type hints, subprocess | Learn Python concepts used in Loom |
| `02-project-overview.md` | Architecture, node types, state machine, data flow | Understand what Loom does |
| `03-running-tests.md` | pytest commands, VS Code test explorer, test structure | Verify everything works |
| `04-tutorial-log-node.md` | Add a `log` node from scratch: code, register, test, run | Hands-on tutorial |
| `05-reference.md` | All node types, config formats, CLI commands, APIs | Quick lookup |
| `06-troubleshooting.md` | Common errors, debug techniques, getting help | Fix problems |
| `07-appendix.md` | uv, pyenv, mypy, ruff, CI/CD, resources | Advanced topics |

## How to Use This Guide

1. **First time?** Start at `00-prerequisites.md` and go through each file in order
2. **Need to add a feature?** Read `02-project-overview.md` then `04-tutorial-log-node.md`
3. **Stuck on an error?** Check `06-troubleshooting.md`
4. **Need API details?** Use `05-reference.md`

## Quick Start (If You Already Know Python)

```bash
cd /Users/hung/Documents/Code/Python/loom
source .venv/bin/activate
pytest                    # Run all tests
loom --help               # See CLI options
```

## Project Status

- **28 tests** passing (original codebase)
- **31 tests** passing (with LogNode tutorial implementation)
- **Python 3.10+** required
- **macOS** primary development platform

---

Start reading: `00-prerequisites.md`
