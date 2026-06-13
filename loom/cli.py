import typer
from pathlib import Path
from loom.executor import GraphExecutor
from loom.state import PipelineState
from loom.config import load_pipeline
from loom.tui import LoomTUI

app = typer.Typer(help="Loom -- Graph-based AI agent pipeline orchestrator")


@app.command()
def main(
    requirement: str = typer.Option(None, "--requirement", "-r", help="Requirement string"),
    pipeline: str = typer.Option("pipeline.yaml", "--pipeline", "-p", help="Pipeline YAML file"),
    resume: bool = typer.Option(False, "--resume", help="Resume from pipeline.state"),
    debug: bool = typer.Option(False, "--debug", help="Show debug state panel"),
):
    """Loom -- Graph-based AI agent pipeline orchestrator."""
    # typer passes the actual value at runtime, but OptionInfo object in tests
    # We need to handle both cases
    if isinstance(pipeline, str):
        pipeline_path = Path(pipeline)
    else:
        # It's an OptionInfo object (typer.testing.CliRunner without invoke)
        pipeline_path = Path(getattr(pipeline, "default", "pipeline.yaml"))
    if not pipeline_path.exists():
        typer.echo(f"Error: {pipeline_path} not found", err=True)
        raise typer.Exit(1)

    config = load_pipeline(pipeline_path)
    executor = GraphExecutor(config)

    if resume:
        state = PipelineState.load(Path("pipeline.state"))
    else:
        if requirement is None:
            requirement = typer.prompt("Enter requirement")
        state = PipelineState(
            current_node=config["entry"],
            visit_counts={},
            shared_state={"requirement": requirement},
        )

    tui = LoomTUI()
    if debug:
        tui.update_state(state.shared_state)

    import asyncio
    final_state = asyncio.run(executor.run(state))
    typer.echo(f"Pipeline completed. Final node: {final_state.current_node}")


if __name__ == "__main__":
    app()
