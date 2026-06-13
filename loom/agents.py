from pathlib import Path
from loom.config import load_agents


class AgentAdapter:
    def __init__(self, agents_path: Path):
        self.agents = load_agents(agents_path)

    def resolve(self, agent_name: str, prompt: str) -> list[str]:
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' not found in agents.yaml")
        agent = self.agents[agent_name]
        binary = agent["binary"]
        cmd = [binary]

        # Hermes CLI uses 'chat -q' for non-interactive mode
        if binary == "hermes" or binary.endswith("/hermes"):
            cmd.extend(["chat", "-q", prompt])
            if "default_model" in agent:
                cmd.extend(["-m", agent["default_model"]])
            # Quiet mode for programmatic use + limit turns
            cmd.extend(["-Q", "--max-turns", "1"])
        else:
            # Generic agent support
            if "default_model" in agent:
                cmd.extend(["--model", agent["default_model"]])
            cmd.extend(["--prompt", prompt])

        return cmd

    def list_agents(self) -> list[str]:
        return list(self.agents.keys())
