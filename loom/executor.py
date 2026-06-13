from pathlib import Path
from loom.state import PipelineState
from loom.nodes.shell import ShellNode
from loom.nodes.agent import AgentNode
from loom.nodes.human import HumanNode
from loom.nodes.condition import ConditionNode
from loom.nodes.subflow import SubflowNode
from loom.nodes.log import LogNode

NODE_REGISTRY = {
    "agent": AgentNode,
    "shell": ShellNode,
    "human": HumanNode,
    "condition": ConditionNode,
    "subflow": SubflowNode,
    "log": LogNode,
}


class GraphExecutor:
    def __init__(self, config: dict, agents_path: Path | None = None):
        self.config = config
        self.entry = config["entry"]
        self.steps = config["steps"]
        self.agents_path = agents_path

    def _create_node(self, name: str):
        step_config = self.steps[name]
        node_type = step_config["type"]
        node_class = NODE_REGISTRY.get(node_type)
        if not node_class:
            raise ValueError(f"Unknown node type: {node_type}")
        return node_class(name=name, config=step_config)

    async def run(self, state: PipelineState) -> PipelineState:
        current = state.current_node or self.entry
        visit_counts = dict(state.visit_counts)
        shared_state = dict(state.shared_state)

        while current:
            # Check max_visits
            max_visits = self.steps[current].get("max_visits")
            visit_counts[current] = visit_counts.get(current, 0) + 1
            if max_visits is not None and visit_counts[current] > max_visits:
                raise RuntimeError(f"Max visits exceeded for node: {current}")

            # Create and run node
            node = self._create_node(current)
            success, output, shared_state = await node.run(shared_state)
            shared_state[f"{current}_output"] = output

            # Persist state before moving to next node
            state = PipelineState(
                current_node=current,
                visit_counts=visit_counts,
                shared_state=shared_state,
            )
            state.save(Path("pipeline.state"))

            # Determine next node
            next_node = node.route(success)
            if not next_node:
                break
            current = next_node

        return state
