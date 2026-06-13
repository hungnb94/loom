import asyncio
from pathlib import Path
from loom.nodes.base import BaseNode


class ShellNode(BaseNode):
    """Execute shell commands sequentially, stopping on first failure.
    Supports configurable timeout per command (default: 300s).
    """

    DEFAULT_TIMEOUT = 300

    async def run(self, state: dict) -> tuple[bool, str, dict]:
        commands = self.config.get("commands", [])
        timeout = self.config.get("timeout", self.DEFAULT_TIMEOUT)
        outputs = []
        for cmd_template in commands:
            cmd = self.render(cmd_template, state)
            try:
                proc = await asyncio.wait_for(
                    asyncio.create_subprocess_shell(
                        cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=Path.cwd(),
                    ),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                outputs.append(f"Command timed out after {timeout}s: {cmd}")
                return False, "\n".join(outputs), state
            stdout, stderr = await proc.communicate()
            outputs.append(stdout.decode() + stderr.decode())
            if proc.returncode != 0:
                return False, "\n".join(outputs), state
        return True, "\n".join(outputs), state
