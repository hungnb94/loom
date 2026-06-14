"""Rich TUI for Loom pipeline visualization."""

from __future__ import annotations

import asyncio
from collections import deque

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
        self._streams: dict[str, deque[str]] = {}
        self.state: dict = {}

    def update_node_status(self, name: str, status: str) -> None:
        """Update the status of a pipeline node."""
        self.nodes[name] = status

    MAX_STREAM_CHARS = 10000

    def update_streaming(self, name: str, output: str) -> None:
        """Append streaming output for a node, capped at max length via chunk buffer."""
        if name not in self._streams:
            self._streams[name] = deque()
        self._streams[name].append(output)
        # Trim old chunks when total exceeds limit
        buf = self._streams[name]
        total = sum(len(c) for c in buf)
        while total > self.MAX_STREAM_CHARS and len(buf) > 1:
            removed = buf.popleft()
            total -= len(removed)

    def _get_stream(self, name: str) -> str:
        """Join chunks into a single string (call only during render)."""
        buf = self._streams.get(name)
        if buf is None:
            return ""
        return "".join(buf)

    def update_state(self, state: dict) -> None:
        """Update global pipeline state."""
        self.state = state

    @property
    def streams(self) -> dict[str, str]:
        """Backward-compatible view: returns joined strings (read-only)."""
        return {name: self._get_stream(name) for name in self._streams}

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
            output = self._get_stream(name)
            tail = output[-80:] if len(output) > 80 else output
            table.add_row(
                name,
                f"[{style}]{status}[/{style}]",
                tail,
            )

        return Panel(table, title="Loom")

    async def run_live(self, refresh_per_second: int = 4) -> None:
        """Run a live-updating TUI display (blocks until interrupted)."""
        with Live(self.render(), console=self.console,
                  refresh_per_second=refresh_per_second) as live:
            try:
                while True:
                    live.update(self.render())
                    await asyncio.sleep(1.0 / refresh_per_second)
            except KeyboardInterrupt:
                pass
