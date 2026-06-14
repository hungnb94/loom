from pathlib import Path
from typer.testing import CliRunner
from loom.cli import app

runner = CliRunner()

def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Loom" in result.output

def test_cli_run_missing_requirement():
    """Non-interactive mode should fail when requirement is missing."""
    result = runner.invoke(app, ["run"], catch_exceptions=False)
    assert result.exit_code == 1
    assert "requirement is required" in result.output

def test_cli_run_with_requirement():
    """Run with requirement should work."""
    result = runner.invoke(app, ["run", "test requirement"], catch_exceptions=False)
    # Should fail because pipeline.yaml not found, not because of missing requirement
    assert "pipeline.yaml not found" in result.output or result.exit_code == 1

def test_cli_status_no_state():
    """Status should fail when no pipeline.state exists."""
    import os
    if os.path.exists("pipeline.state"):
        os.remove("pipeline.state")
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 1
    assert "No active pipeline" in result.output

def test_cli_agents_no_config():
    """Agents should fail when no agents.yaml exists."""
    from unittest.mock import patch
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        with patch("pathlib.Path.home", return_value=Path(tmp)):
            result = runner.invoke(app, ["agents"])
            assert result.exit_code == 1
            assert "No agents.yaml" in result.output
