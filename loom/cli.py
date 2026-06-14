import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import typer
from loom.executor import GraphExecutor
from loom.state import PipelineState
from loom.config import load_pipeline
from loom.tui import LoomTUI

app = typer.Typer(help="Loom -- Graph-based AI agent pipeline orchestrator")


def _resolve_option(value, fallback):
    """Resolve typer.Option value — handles both runtime values and OptionInfo objects."""
    if isinstance(value, (str, bool)) or value is None:
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
def graph(
    pipeline: str = typer.Option("pipeline.yaml", "--pipeline", "-p", help="Pipeline YAML file"),
):
    """Visualize pipeline as ASCII graph."""
    pipeline_path = Path(_resolve_option(pipeline, "pipeline.yaml"))
    if not pipeline_path.exists():
        typer.echo(f"Error: {pipeline_path} not found", err=True)
        raise typer.Exit(1)

    from loom.graph import render_graph

    config = load_pipeline(pipeline_path)
    typer.echo(render_graph(config))


@app.command()
def output(
    node: Optional[str] = typer.Argument(None, help="Node name to show output for (omit for all)"),
    last: bool = typer.Option(False, "--last", "-l", help="Show only the last node's output"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """Show node outputs from the last pipeline run."""
    state_path = Path("pipeline.state")
    if not state_path.exists():
        typer.echo("No pipeline.state found. Run a pipeline first.", err=True)
        raise typer.Exit(1)

    state = PipelineState.load(state_path)
    shared = state.shared_state

    outputs = {k: v for k, v in shared.items() if k.endswith("_output")}

    if not outputs:
        typer.echo("No node outputs found in state.", err=True)
        raise typer.Exit(1)

    if last:
        # Find the last executed node from current_node
        node_name = state.current_node
        output_key = f"{node_name}_output"
        if output_key in outputs:
            outputs = {node_name: outputs[output_key]}
        else:
            typer.echo(f"No output found for node '{node_name}'", err=True)
            raise typer.Exit(1)
    elif node:
        output_key = f"{node}_output"
        if output_key not in outputs:
            typer.echo(f"Node '{node}' not found. Available: {', '.join(k.replace('_output', '') for k in outputs)}", err=True)
            raise typer.Exit(1)
        outputs = {node: outputs[output_key]}

    if json_output:
        typer.echo(json.dumps(outputs, indent=2))
    else:
        for node_name, content in outputs.items():
            typer.echo(f"── {node_name} ──")
            typer.echo(content.rstrip())
            typer.echo()


@app.command()
def validate(
    pipeline: str = typer.Option("pipeline.yaml", "--pipeline", "-p", help="Pipeline YAML file"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """Validate a pipeline YAML file without running it."""
    pipeline_path = Path(_resolve_option(pipeline, "pipeline.yaml"))

    if not pipeline_path.exists():
        typer.echo(f"Error: {pipeline_path} not found", err=True)
        raise typer.Exit(1)

    try:
        config = load_pipeline(pipeline_path)

        if json_output:
            typer.echo(json.dumps({"valid": True, "file": str(pipeline_path)}))
        else:
            typer.echo(f"✓ {pipeline_path} is valid")
            steps = config.get("steps", {})
            node_types = {}
            for name, step in steps.items():
                t = step.get("type", "?")
                node_types[t] = node_types.get(t, 0) + 1
            typer.echo(f"  {len(steps)} nodes: {', '.join(f'{t}×{c}' for t, c in node_types.items())}")
    except ValueError as e:
        if json_output:
            typer.echo(json.dumps({"valid": False, "errors": str(e).split("; ")}))
        else:
            typer.echo(f"✗ {pipeline_path} has errors:", err=True)
            for err in str(e).split("; "):
                typer.echo(f"  • {err}", err=True)
        raise typer.Exit(1)


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
