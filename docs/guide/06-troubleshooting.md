# Troubleshooting

Common errors you might encounter and how to fix them.

---

## Installation Issues

### "command not found: python"

Python might be installed as `python3` on your system:

```bash
python3 --version
```

If `python3` works but `python` doesn't, create an alias or use `python3` everywhere:

```bash
alias python=python3
```

Add to `~/.zshrc` to make it permanent.

### "pip not found"

```bash
python -m ensurepip --upgrade
python -m pip install --upgrade pip
```

Or with Homebrew:

```bash
brew install python  # pip is included
```

### "ERROR: Could not build wheels for ..."

Some packages need compilation. On macOS:

```bash
xcode-select --install
```

---

## Virtual Environment Issues

### "No module named 'loom'"

You forgot to activate the virtual environment:

```bash
source .venv/bin/activate
```

Or you installed in a different environment. Check:

```bash
which python
# Should show: /Users/hung/Documents/Code/Python/loom/.venv/bin/python
```

### "Requirement already satisfied" but import fails

You might have multiple Python installations. Check:

```bash
python -c "import sys; print(sys.path)"
python -c "import loom; print(loom.__file__)"
```

---

## Test Failures

### "pytest not found"

Install dev dependencies:

```bash
pip install -e ".[dev]"
```

### "ImportError: cannot import name 'LogNode'"

You forgot to add the import in `loom/executor.py`:

```python
from loom.nodes.log import LogNode
```

### "RuntimeError: Event loop is closed"

This happens when mixing sync and async code incorrectly. In tests, always use `@pytest.mark.asyncio`:

```python
@pytest.mark.asyncio
async def test_something():
    # ...
```

### "AssertionError" with no clear message

Add a message to your assert:

```python
assert success is True, f"Expected success but got {success}"
```

Run with verbose mode:

```bash
pytest -v --tb=long
```

---

## Pipeline Issues

### "Error: pipeline.yaml not found"

Make sure you're in the project directory:

```bash
cd /Users/hung/Documents/Code/Python/loom
loom --requirement "test"
```

Or specify the full path:

```bash
loom --pipeline /Users/hung/Documents/Code/Python/loom/examples/pipeline.yaml
```

### "ValueError: pipeline config must have 'entry' node"

Your `pipeline.yaml` is missing the `entry` field:

```yaml
entry: clarify  # <-- Add this at the top

steps:
  clarify:
    # ...
```

### "ValueError: Step 'xyz' must have 'type'"

Every step in `steps` must have a `type` field:

```yaml
steps:
  my_step:
    type: shell  # <-- Required
    commands:
      - echo hello
```

### "RuntimeError: Max visits exceeded for node: verify"

A node is looping too many times. Check your pipeline logic:

```yaml
verify:
  type: shell
  commands:
    - yarn test
  on_pass: review
  on_fail: fix_code
  max_visits: 5  # <-- Increase or fix the loop

fix_code:
  type: agent
  # ...
  next: verify  # <-- This creates a loop
```

If `verify` fails, it goes to `fix_code`, then back to `verify`. If `verify` keeps failing, it will hit `max_visits`. This is intentional — it prevents infinite loops.

---

## Agent Issues

### "Agent 'claude' not found in agents.yaml"

Create `~/.loom/agents.yaml`:

```bash
mkdir -p ~/.loom
cat > ~/.loom/agents.yaml << 'EOF'
agents:
  claude:
    binary: claude
    default_model: claude-sonnet-4-6
    api_key_env: ANTHROPIC_API_KEY
EOF
```

### "claude: command not found"

Install the Claude CLI:

```bash
# Via npm (if available)
npm install -g @anthropic-ai/claude-cli

# Or download from Anthropic's website
```

Verify:

```bash
which claude
claude --version
```

---

## Debug Techniques

### Print Debugging

Add `print()` statements and run with `-s`:

```python
async def run(self, state):
    print(f"DEBUG: state = {state}")
    # ...
```

```bash
pytest -s
```

### VS Code Debugger

1. Set a breakpoint (click left of line number)
2. Run → Start Debugging (F5)
3. Select "Python" → "pytest"

### Inspect pipeline.state

```bash
cat pipeline.state | python -m json.tool
```

### Check Node Output

```python
# In a test or script
node = ShellNode(name="test", config={"commands": ["echo hello"]})
success, output, state = asyncio.run(node.run({}))
print(f"success={success}, output={output!r}")
```

---

## Getting Help

If you're stuck:

1. Read the error message carefully — Python errors usually tell you exactly what's wrong
2. Check the line number in the traceback
3. Search the codebase for similar patterns
4. Run `pytest -v --tb=long` for full context
5. Add `print()` or use the VS Code debugger

---

## Next Step

Go to `07-appendix.md` for advanced topics: uv, pyenv, CI/CD, and more.
