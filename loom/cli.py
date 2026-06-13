import typer
import json
import sys
from pathlib import Path
from typing import Optional
from loom.executor import GraphExecutor
from loom.state import PipelineState
from loom.config import load_pipeline
from loom.tui import LoomTUI

app = typer.Typer(help="Loom -- Graph-based AI agent pipeline orchestrator")


def _resolve_option(value, fallback):
    """Resolve typer.Option value — handles both runtime values and OptionInfo objects."""
    if isinstance(value, str) or isinstance(value, bool) or value is None:
        return value
    # OptionInfo object from typer.testing.CliRunner
    return getattr(value, "default", fallback)


@app.command()
def run(
    requirement: Optional[str] = typer.Argument(None, help="Requirement string (optional)"),
    pipeline: str = typer.Option("pipeline.yaml", "--pipeline", "-p", help="Pipeline YAML file"),
    resume: bool = typer.Option(False, "--resume", help="Resume from pipeline.state"),
    debug: bool = typer.Option(False, "--debug", help="Show debug state panel"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output final state as JSON"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Silent mode — only output errors and final result"),
    no_tui: bool = typer.Option(False, "--no-tui", help="Disable TUI, use plain text output"),
):
    """Run a Loom pipeline."""
    pipeline_path = Path(_resolve_option(pipeline, "pipeline.yaml"))
    resume = _resolve_option(resume, False)
    debug = _resolve_option(debug, False)
    json_output = _resolve_option(json_output, False)
    quiet = _resolve_option(quiet, False)
    no_tui = _resolve_option(no_tui, False)

    state = None
    if resume:
        state_path = Path("pipeline.state")
        if not state_path.exists():
            if not quiet:
                typer.echo("Error: pipeline.state not found, cannot resume", err=True)
            raise typer.Exit(1)
        state = PipelineState.load(state_path)
    else:
        if requirement is None:
            # Non-interactive mode: requirement is required
            if not quiet:
                typer.echo("Error: requirement is required. Use: loom run 'your requirement'", err=True)
            raise typer.Exit(1)
        state = PipelineState(
            current_node="",
            visit_counts={},
            shared_state={"requirement": requirement},
        )

    if not pipeline_path.exists():
        if not quiet:
            typer.echo(f"Error: {pipeline_path} not found", err=True)
        raise typer.Exit(1)

    config = load_pipeline(pipeline_path)
    executor = GraphExecutor(config)

    if state.current_node is None:
        state.current_node = config["entry"]

    tui = None
    if not no_tui and not quiet:
        tui = LoomTUI()
        if debug:
            tui.update_state(state.shared_state)

    import asyncio
    try:
        final_state = asyncio.run(executor.run(state, tui=tui, quiet=quiet))
    except RuntimeError as e:
        if not quiet:
            typer.echo(f"Pipeline failed: {e}", err=True)
        raise typer.Exit(2)
    except Exception as e:
        if not quiet:
            typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(3)

    if json_output:
        output = {
            "current_node": final_state.current_node,
            "visit_counts": final_state.visit_counts,
            "shared_state": final_state.shared_state,
            "success": final_state.current_node not in config.get("failure_nodes", []),
        }
        typer.echo(json.dumps(output, indent=2))
    elif not quiet:
        typer.echo(f"Pipeline completed. Final node: {final_state.current_node}")


@app.command()
def status(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """Show current pipeline status from pipeline.state."""
    state_path = Path("pipeline.state")
    if not state_path.exists():
        typer.echo("No active pipeline found.", err=True)
        raise typer.Exit(1)

    state = PipelineState.load(state_path)
    if json_output:
        typer.echo(json.dumps({
            "current_node": state.current_node,
            "visit_counts": state.visit_counts,
            "shared_state": state.shared_state,
        }, indent=2))
    else:
        typer.echo(f"Current node: {state.current_node}")
        typer.echo(f"Visit counts: {state.visit_counts}")


@app.command()
def agents(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """List registered agents from ~/.loom/agents.yaml."""
    agents_path = Path.home() / ".loom" / "agents.yaml"
    if not agents_path.exists():
        typer.echo("No agents.yaml found at ~/.loom/agents.yaml", err=True)
        raise typer.Exit(1)

    from loom.agents import AgentAdapter
    adapter = AgentAdapter(agents_path)
    agent_list = adapter.list_agents()

    if json_output:
        typer.echo(json.dumps({"agents": agent_list}, indent=2))
    else:
        typer.echo("Registered agents:")
        for name in agent_list:
            typer.echo(f"  - {name}")


def main():
    app()


if __name__ == "__main__":
    main()
