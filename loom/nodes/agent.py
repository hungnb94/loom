import asyncio
from pathlib import Path
from loom.nodes.base import BaseNode
from loom.agents import AgentAdapter


class AgentNode(BaseNode):
    """Spawn an agent subprocess and evaluate its output for pass/fail."""

    _adapter_cache: AgentAdapter | None = None
    _agents_path_mtime: float | None = None

    async def run(self, state: dict) -> tuple[bool, str, dict]:
        prompt = self.render(self.config.get("prompt", ""), state)
        agent_name = self.config.get("agent", "echo")
        pass_keyword = self.config.get("pass_keyword", "PASS")

        # Resolve agent command from agents.yaml with caching
        agents_path = Path.home() / ".loom" / "agents.yaml"
        cmd = self._resolve_cmd(agents_path, agent_name, prompt)

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        output = stdout.decode() + stderr.decode()
        return pass_keyword in output, output, state

    @classmethod
    def _resolve_cmd(cls, agents_path: Path, agent_name: str, prompt: str) -> list[str]:
        if not agents_path.exists():
            return [agent_name, prompt]

        # Check mtime for cache invalidation
        mtime = agents_path.stat().st_mtime
        if cls._adapter_cache is None or cls._agents_path_mtime != mtime:
            cls._adapter_cache = AgentAdapter(agents_path)
            cls._agents_path_mtime = mtime

        try:
            return cls._adapter_cache.resolve(agent_name, prompt)
        except ValueError:
            return [agent_name, prompt]
