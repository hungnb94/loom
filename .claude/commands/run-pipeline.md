Run a pipeline YAML file step by step, enforcing sequential execution.

## Arguments

`$ARGUMENTS` format: `[pipeline_file] <requirement>`

- If one token: treat as requirement, use `examples/pipeline.yaml` as pipeline.
- If first token ends with `.yaml`: first token = pipeline file, rest = requirement.

## Instructions

### 1. Parse arguments

Parse `$ARGUMENTS` to extract `pipeline_file` and `requirement`.

### 2. Load pipeline

Read the pipeline YAML file. Confirm it's valid (has `entry` and `steps` keys). If not found, tell the user and stop.

### 3. Initialize state

Write `.claude/pipeline.state`:

```json
{
  "mode": "pipeline",
  "pipeline": "<pipeline_file>",
  "current_step": "<entry_step>",
  "completed_steps": [],
  "requirement": "<requirement>",
  "shared_state": {
    "requirement": "<requirement>"
  }
}
```

### 4. Execute steps sequentially

For each step, starting from `entry`:

**Render the prompt** — replace `{{variable}}` in the step's prompt with values from `shared_state`.

**Execute based on type:**

- `type: agent, agent: claude` — Execute the rendered prompt directly. Your response IS the step output. Check output for `pass_keyword` at the start of a line to determine pass/fail.

- `type: agent, agent: <other>` — Run via Bash:
  ```
  <agent_binary> "<rendered_prompt>"
  ```
  Capture output. Check for `pass_keyword`.

- `type: shell` — Run each command in sequence via Bash. All must exit 0 for pass; any non-zero = fail. Capture combined output.

**Determine routing:**
- If pass and `on_pass` exists → next = `on_pass`
- If fail and `on_fail` exists → next = `on_fail`
- If `next` exists (unconditional) → next = `next`
- If none → pipeline complete

**Check max_visits** — if `max_visits` is set and this step has been visited that many times, stop and report error.

**Update state after each step** using the Bash tool:

```bash
python3 -c "
import json
from pathlib import Path
p = Path('.claude/pipeline.state')
s = json.loads(p.read_text())
s['completed_steps'].append('<current_step>')
s['current_step'] = '<next_step>'
s['shared_state']['<current_step>_output'] = '''<output>'''
p.write_text(json.dumps(s, indent=2))
"
```

### 5. Terminal node

When a step has `terminal: true`, after executing it:
- Update `completed_steps`
- Set `mode` to `"free"` in state file
- Report pipeline complete to user
