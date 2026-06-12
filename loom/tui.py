"""Rich TUI for Loom pipeline visualization."""

from __future__ import annotations

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class LoomTUI:
    """Terminal UI showing pipeline progress, node statuses, and streaming output."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()
        self.nodes: dict[str, str] = {}
        self.streams: dict[str, str] = {}
        self.state: dict = {}

    def update_node_status(self, name: str, status: str) -> None:
        """Update the status of a pipeline node."""
        self.nodes[name] = status

    def update_streaming(self, name: str, output: str) -> None:
        """Append streaming output for a node."""
        self.streams[name] = self.streams.get(name, "") + output

    def update_state(self, state: dict) -> None:
        """Update global pipeline state."""
        self.state = state

    def render(self) -> Panel:
        """Render the current TUI state as a Rich Panel."""
        table = Table(title="Loom Pipeline")
        table.add_column("Node", style="cyan")
        table.add_column("Status", style="green")

        status_styles: dict[str, str] = {
            "pending": "yellow",
            "running": "blue",
            "completed": "green",
            "failed": "red",
        }

        for name, status in self.nodes.items():
            style = status_styles.get(status, "white")
            table.add_row(name, f"[{style}]{status}[/{style}]")

        # Append streaming outputs as additional rows if any
        if self.streams:
            table.add_column("Output", style="dim")
            for name, output in self.streams.items():
                # Show last 80 chars of streaming output
                tail = output[-80:] if len(output) > 80 else output
                style = status_styles.get(self.nodes.get(name, ""), "white")
                table.add_row(
                    name,
                    f"[{style}]{self.nodes.get(name, 'running')}[/{style}]",
                    tail,
                )

        return Panel(table, title="Loom")

    def run_live(self) -> None:
        """Run a live-updating TUI display (blocks until interrupted)."""
        with Live(self.render(), console=self.console, refresh_per_second=4) as live:
            while True:
                live.update(self.render())
                # In real implementation, this would be event-driven
                break
