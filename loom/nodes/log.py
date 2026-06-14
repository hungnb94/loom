from typing import Any

import asyncio
from pathlib import Path
from loom.nodes.base import BaseNode


class LogNode(BaseNode):
    """Write a Jinja2-rendered log message to a file."""

    async def run(self, state: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        message = self.render(self.config.get("message", ""), state)
        file_path = Path(self.config.get("file", "loom.log"))
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._write_log, file_path, message)
        return True, f"Logged to {file_path}", state

    @staticmethod
    def _write_log(file_path: Path, message: str) -> None:
        # Ensure parent directory exists to prevent FileNotFoundError
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(message + "\n")
