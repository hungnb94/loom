# Appendix

Advanced topics, tools, and resources.

---

## A. uv (Modern Python Package Manager)

uv is a Python package manager written in Rust. It's 10-100x faster than pip.

### Install

```bash
brew install uv
```

### Create Virtual Environment

```bash
uv venv
source .venv/bin/activate
```

### Install Dependencies

```bash
uv pip install -e ".[dev]"
```

### Lock Dependencies

```bash
uv pip compile pyproject.toml -o requirements.txt
```

### Sync (Install from Lock File)

```bash
uv pip sync requirements.txt
```

---

## B. pyenv Advanced

### Install Multiple Python Versions

```bash
pyenv install 3.11
pyenv install 3.12
pyenv install 3.13
```

### Switch Versions

```bash
pyenv global 3.12    # System-wide default
pyenv local 3.11     # Per-project (creates .python-version file)
pyenv shell 3.13     # Current shell only
```

### List Installed Versions

```bash
pyenv versions
```

### Update pyenv

```bash
brew upgrade pyenv
```

---

## C. Type Checking with mypy

mypy checks type hints without running code:

```bash
pip install mypy
mypy loom/
```

Add to `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
```

---

## D. Code Formatting with ruff

ruff is a fast Python linter and formatter:

```bash
pip install ruff
ruff check loom/          # Lint
ruff check --fix loom/    # Lint and auto-fix
ruff format loom/         # Format
```

Add to `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W"]
```

---

## E. Git Hooks with pre-commit

pre-commit runs checks before each commit:

```bash
pip install pre-commit
pre-commit install
```

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
```

---

## F. CI/CD with GitHub Actions

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run tests
        run: pytest

      - name: Run type check
        run: mypy loom/

      - name: Run linter
        run: ruff check loom/
```

---

## G. Useful Resources

### Python

- [Python Official Tutorial](https://docs.python.org/3/tutorial/)
- [Real Python](https://realpython.com/) — Tutorials for all levels
- [Python Type Hints Cheat Sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)

### Async Python

- [Async IO in Python](https://realpython.com/async-io-python/)
- [asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

### Testing

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)

### Tools Used in Loom

- [Typer](https://typer.tiangolo.com/) — CLI framework
- [Rich](https://rich.readthedocs.io/) — Terminal UI
- [PyYAML](https://pyyaml.org/wiki/PyYAMLDocumentation) — YAML parsing
- [Jinja2](https://jinja.palletsprojects.com/) — Templates

---

## H. Project-Specific Conventions

### Code Style

- Type hints on all function signatures
- `async def` for all node `run()` methods
- `Path` instead of string paths
- `dict.get()` with defaults instead of `dict[key]` when key might be missing

### Testing Conventions

- One test file per module (`loom/nodes/shell.py` → `tests/test_nodes.py`)
- `@pytest.mark.asyncio` on all async tests
- Use `tempfile.TemporaryDirectory()` for file operations
- Mock external dependencies (subprocess, API calls)

### Commit Messages

Follow conventional commits:

```
feat: add log node
test: add tests for log node
docs: update developer guide
fix: handle missing file in log node
refactor: extract template rendering to helper
```

---

## End of Guide

You now have a complete understanding of Loom from zero to adding features. Go build something!
