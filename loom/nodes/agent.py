import asyncio
from pathlib import Path
from loom.nodes.base import BaseNode
from loom.agents import AgentAdapter


class AgentNode(BaseNode):
    """Spawn an agent subprocess and evaluate its output for pass/fail."""

    async def run(self, state: dict) -> tuple[bool, str, dict]:
        prompt = self.render(self.config.get("prompt", ""), state)
        agent_name = self.config.get("agent", "echo")
        pass_keyword = self.config.get("pass_keyword", "PASS")

        # Resolve agent command from agents.yaml
        agents_path = Path.home() / ".loom" / "agents.yaml"
        if agents_path.exists():
            adapter = AgentAdapter(agents_path)
            try:
                cmd = adapter.resolve(agent_name, prompt)
            except ValueError:
                cmd = [agent_name, prompt]
        else:
            cmd = [agent_name, prompt]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        output = stdout.decode() + stderr.decode()
        return pass_keyword in output, output, state
