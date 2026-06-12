import asyncio
from loom.nodes.base import BaseNode


class AgentNode(BaseNode):
    """Spawn an agent subprocess and evaluate its output for pass/fail."""

    async def run(self, state):
        prompt = self.config.get("prompt", "")
        agent = self.config.get("agent", "echo")
        pass_keyword = self.config.get("pass_keyword", "PASS")

        proc = await asyncio.create_subprocess_exec(
            agent, prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode()
        success = pass_keyword in output
        return success, output, state
