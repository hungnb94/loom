"""Node type registry — single source of truth for all node implementations.

Extracted from executor.py to eliminate circular imports (parallel.py → executor → nodes).
"""

from loom.nodes.agent import AgentNode
from loom.nodes.shell import ShellNode
from loom.nodes.condition import ConditionNode
from loom.nodes.subflow import SubflowNode
from loom.nodes.log import LogNode
from loom.nodes.parallel import ParallelNode

NODE_REGISTRY: dict[str, type] = {
    "agent": AgentNode,
    "shell": ShellNode,
    "condition": ConditionNode,
    "subflow": SubflowNode,
    "log": LogNode,
    "parallel": ParallelNode,
}
