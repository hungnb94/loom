import pytest
from pathlib import Path
from loom.config import load_pipeline, validate_pipeline


# ── Valid pipeline ──
VALID_PIPELINE = {
    "entry": "start",
    "steps": {
        "start": {"type": "shell", "commands": ["echo hi"], "on_pass": "end"},
        "end": {"type": "shell", "commands": ["echo done"]},
    },
}


def test_valid_pipeline_passes():
    validate_pipeline(VALID_PIPELINE)


def test_missing_entry():
    with pytest.raises(ValueError, match="entry"):
        validate_pipeline({"steps": {}})


def test_missing_steps():
    with pytest.raises(ValueError, match="steps"):
        validate_pipeline({"entry": "x"})


def test_step_missing_type():
    with pytest.raises(ValueError, match="type"):
        validate_pipeline({"entry": "a", "steps": {"a": {"commands": []}}})


def test_unknown_node_type():
    with pytest.raises(ValueError, match="unknown node type"):
        validate_pipeline({"entry": "a", "steps": {"a": {"type": "alien"}}})


def test_edge_reference_nonexistent():
    with pytest.raises(ValueError, match="references non-existent node"):
        validate_pipeline({"entry": "a", "steps": {
            "a": {"type": "shell", "commands": ["echo"], "on_pass": "ghost"}
        }})


def test_entry_not_in_steps():
    with pytest.raises(ValueError, match="entry|not in steps"):
        validate_pipeline({"entry": "missing", "steps": {
            "exists": {"type": "shell", "commands": ["echo"]}
        }})


def test_shell_node_requires_commands():
    with pytest.raises(ValueError, match="commands"):
        validate_pipeline({"entry": "a", "steps": {
            "a": {"type": "shell"}
        }})


def test_agent_node_requires_agent():
    with pytest.raises(ValueError, match="agent"):
        validate_pipeline({"entry": "a", "steps": {
            "a": {"type": "agent", "prompt": "hi"}
        }})


def test_agent_node_requires_prompt():
    with pytest.raises(ValueError, match="prompt"):
        validate_pipeline({"entry": "a", "steps": {
            "a": {"type": "agent", "agent": "hermes"}
        }})


def test_condition_node_requires_expression():
    with pytest.raises(ValueError, match="expression"):
        validate_pipeline({"entry": "a", "steps": {
            "a": {"type": "condition"}
        }})


def test_condition_node_requires_edges():
    with pytest.raises(ValueError, match="on_true|on_false"):
        validate_pipeline({"entry": "a", "steps": {
            "a": {"type": "condition", "expression": "True"}
        }})


def test_log_node_requires_message():
    with pytest.raises(ValueError, match="message"):
        validate_pipeline({"entry": "a", "steps": {
            "a": {"type": "log"}
        }})


def test_parallel_node_requires_branches():
    with pytest.raises(ValueError, match="branches"):
        validate_pipeline({"entry": "a", "steps": {
            "a": {"type": "parallel"}
        }})


def test_jinja2_syntax_error():
    with pytest.raises(ValueError, match="template|jinja|Jinja2"):
        validate_pipeline({"entry": "a", "steps": {
            "a": {"type": "shell", "commands": ["echo {{unclosed"]}
        }})


def test_unreachable_nodes():
    with pytest.raises(ValueError, match="unreachable"):
        validate_pipeline({"entry": "a", "steps": {
            "a": {"type": "shell", "commands": ["echo"], "on_pass": "b"},
            "b": {"type": "shell", "commands": ["echo"]},
            "orphan": {"type": "shell", "commands": ["echo"]},
        }})


def test_multiple_errors_collected():
    """validate_pipeline should collect multiple errors, not stop at first."""
    with pytest.raises(ValueError) as exc_info:
        validate_pipeline({"entry": "x", "steps": {
            "a": {"type": "alien"},
        }})
    msg = str(exc_info.value)
    # Should mention both entry mismatch AND unknown type
    assert "entry" in msg.lower() or "alien" in msg


def test_human_node_valid():
    validate_pipeline({"entry": "a", "steps": {
        "a": {"type": "human", "on_approve": "b"},
        "b": {"type": "shell", "commands": ["echo"]},
    }})


def test_subflow_node_valid():
    validate_pipeline({"entry": "a", "steps": {
        "a": {"type": "subflow", "pipeline": "other.yaml"},
    }})


def test_human_node_on_timeout_valid():
    """on_timeout edge should be validated like other edge keys."""
    validate_pipeline({"entry": "a", "steps": {
        "a": {"type": "human", "on_approve": "b", "on_timeout": "c"},
        "b": {"type": "shell", "commands": ["echo ok"]},
        "c": {"type": "shell", "commands": ["echo timeout"]},
    }})


def test_on_timeout_references_nonexistent():
    """on_timeout referencing a non-existent node should fail validation."""
    with pytest.raises(ValueError, match="references non-existent node"):
        validate_pipeline({"entry": "a", "steps": {
            "a": {"type": "human", "on_approve": "b", "on_timeout": "ghost"},
            "b": {"type": "shell", "commands": ["echo ok"]},
        }})
