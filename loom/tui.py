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

    MAX_STREAM_LEN = 10000

    def update_streaming(self, name: str, output: str) -> None:
        """Append streaming output for a node, capped at max length."""
        current = self.streams.get(name, "")
        combined = current + output
        if len(combined) > self.MAX_STREAM_LEN:
            combined = combined[-self.MAX_STREAM_LEN:]
        self.streams[name] = combined

    def update_state(self, state: dict) -> None:
        """Update global pipeline state."""
        self.state = state

    def render(self) -> Panel:
        """Render the current TUI state as a Rich Panel."""
        table = Table(title="Loom Pipeline")
        table.add_column("Node", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Output", style="dim")

        status_styles: dict[str, str] = {
            "pending": "yellow",
            "running": "blue",
            "completed": "green",
            "failed": "red",
        }

        for name, status in self.nodes.items():
            style = status_styles.get(status, "white")
            output = self.streams.get(name, "")
            tail = output[-80:] if len(output) > 80 else output
            table.add_row(
                name,
                f"[{style}]{status}[/{style}]",
                tail,
            )

        return Panel(table, title="Loom")

    def run_live(self, refresh_per_second: int = 4) -> None:
        """Run a live-updating TUI display (blocks until interrupted)."""
        import time
        with Live(self.render(), console=self.console,
                  refresh_per_second=refresh_per_second) as live:
            try:
                while True:
                    live.update(self.render())
                    time.sleep(1.0 / refresh_per_second)
            except KeyboardInterrupt:
                pass
