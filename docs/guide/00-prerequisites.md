# Prerequisites

This guide assumes you are starting from zero Python knowledge but already know:
- **Terminal basics** (`cd`, `ls`, `mkdir`, `cat`)
- **Git** (`clone`, `commit`, `push`, `branch`)
- **JSON** structure (`{"key": "value"}`)
- **Async programming** concept (promises/callbacks from JavaScript — we'll map this to Python)

You will need:
- macOS (this guide is written for macOS; Linux is similar, Windows needs WSL)
- VS Code (with Python extension)
- A terminal

---

## 1. Install Python

### Option A: Homebrew (Fast, Good Enough)

Homebrew is a package manager for macOS. If you don't have it:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Then install Python:

```bash
brew install python
python3 --version   # Should show 3.10 or higher
```

### Option B: pyenv (Recommended for Serious Development)

pyenv lets you install multiple Python versions and switch between them.

```bash
brew install pyenv
```

Add to your shell profile (`~/.zshrc`):

```bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
source ~/.zshrc
```

Install Python 3.12 (latest stable at time of writing):

```bash
pyenv install 3.12
pyenv global 3.12
python --version   # Should show 3.12.x
```

---

## 2. Install VS Code & Python Extension

1. Download VS Code: https://code.visualstudio.com/
2. Open VS Code → Extensions (Cmd+Shift+X) → Search "Python" → Install the one by Microsoft
3. Open VS Code → Extensions → Search "Python Test Explorer" → Install (optional but helpful)

---

## 3. Clone the Loom Repository

```bash
cd ~/Documents/Code/Python   # or wherever you keep code
git clone <repository-url> loom
cd loom
```

---

## 4. Set Up Virtual Environment

A virtual environment isolates this project's dependencies from your system Python.

### Using venv (Built-in, Tutorial Path)

```bash
python -m venv .venv
source .venv/bin/activate
```

Your prompt should now show `(.venv)` at the beginning.

### Using uv (Advanced, Faster)

uv is a modern Python package manager written in Rust. It's much faster than pip.

```bash
brew install uv
uv venv
source .venv/bin/activate
```

---

## 5. Install Project Dependencies

```bash
pip install -e ".[dev]"
```

This installs:
- `typer` — CLI framework
- `rich` — Terminal UI
- `pyyaml` — YAML parsing
- `jinja2` — Template engine
- `pytest` — Testing framework
- `pytest-asyncio` — Async test support

Verify installation:

```bash
loom --help
```

You should see the Loom CLI help output.

---

## Next Step

Go to `01-python-crash-course.md` to learn the Python concepts used in this project.
