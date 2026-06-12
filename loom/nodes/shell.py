import asyncio
from loom.nodes.base import BaseNode


class ShellNode(BaseNode):
    """Execute shell commands sequentially, stopping on first failure."""

    async def run(self, state):
        commands = self.config.get("commands", [])
        outputs = []
        for cmd in commands:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            outputs.append(stdout.decode() + stderr.decode())
            if proc.returncode != 0:
                return False, "\n".join(outputs), state
        return True, "\n".join(outputs), state
