from pathlib import Path
from loom.nodes.base import BaseNode


class LogNode(BaseNode):
    """Write a Jinja2-rendered log message to a file."""

    async def run(self, state: dict) -> tuple[bool, str, dict]:
        message = self.render(self.config.get("message", ""), state)
        file_path = Path(self.config.get("file", "loom.log"))
        import asyncio
        await asyncio.to_thread(self._write_log, file_path, message)
        return True, f"Logged to {file_path}", state

    @staticmethod
    def _write_log(file_path: Path, message: str) -> None:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(message + "\n")
