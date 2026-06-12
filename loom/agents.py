from pathlib import Path
from loom.config import load_agents

class AgentAdapter:
    def __init__(self, agents_path: Path):
        self.agents = load_agents(agents_path)

    def resolve(self, agent_name: str, prompt: str) -> list[str]:
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' not found in agents.yaml")
        agent = self.agents[agent_name]
        cmd = [agent["binary"]]
        if "default_model" in agent:
            cmd.extend(["--model", agent["default_model"]])
        # Some agents accept prompt via stdin, others via --prompt
        # For now, append as positional arg
        cmd.append(prompt)
        return cmd
