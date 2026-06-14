from typing import Any

import asyncio
from pathlib import Path
from loom.nodes.base import BaseNode


class ShellNode(BaseNode):
    """Execute shell commands sequentially, stopping on first failure.
    Supports configurable timeout per command (default: 300s).

    Security note: Commands are Jinja2-rendered then executed via
    ``subprocess_shell``. Pipeline YAML is developer-authored and trusted.
    User-supplied variables (e.g. ``{{requirement}}``) are interpolated
    directly — never pass untrusted input into shell commands.
    """

    DEFAULT_TIMEOUT = 300

    async def run(self, state: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        commands = self.config.get("commands", [])
        timeout = self.config.get("timeout", self.DEFAULT_TIMEOUT)
        outputs: list[str] = []
        for cmd_template in commands:
            cmd = self.render(cmd_template, state)
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=Path.cwd(),
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                outputs.append(f"Command timed out after {timeout}s: {cmd}")
                return False, "\n".join(outputs), state
            outputs.append(stdout.decode("utf-8", errors="replace") + stderr.decode("utf-8", errors="replace"))
            if proc.returncode != 0:
                return False, "\n".join(outputs), state
        return True, "\n".join(outputs), state
