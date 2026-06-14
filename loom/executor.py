from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from loom.state import PipelineState
from loom.registry import NODE_REGISTRY
from loom.tui import LoomTUI


class GraphExecutor:
    def __init__(self, config: dict, agents_path: Path | None = None, state_path: Path | None = None):
        self.config = config
        self.entry = config["entry"]
        self.steps = config["steps"]
        self.agents_path = agents_path
        self._state_path = state_path or Path("pipeline.state")

    def _create_node(self, name: str):
        step_config = self.steps[name]
        node_class = NODE_REGISTRY.get(step_config["type"])
        if not node_class:
            raise ValueError(f"Unknown node type: {step_config['type']}")
        return node_class(name=name, config=step_config)

    def _check_max_visits(self, node: str, visit_counts: dict) -> None:
        max_visits = self.steps[node].get("max_visits")
        if max_visits is None:
            return
        visits = visit_counts.get(node, 0)
        if visits > max_visits:
            raise RuntimeError(f"Max visits exceeded for node: {node}")

    async def _persist_state(self, state: PipelineState):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, state.save, self._state_path)

    def _update_tui(self, tui, node: str, status: str, output: str = ""):
        if tui is None:
            return
        tui.update_node_status(node, status)
        if output:
            tui.update_streaming(node, output)

    async def run(self, state: PipelineState, tui: LoomTUI | None = None, quiet: bool = False) -> PipelineState:
        current = state.current_node or self.entry
        visit_counts: dict[str, int] = dict(state.visit_counts)
        shared_state: dict[str, Any] = dict(state.shared_state)

        while current:
            visit_counts[current] = visit_counts.get(current, 0) + 1
            self._check_max_visits(current, visit_counts)

            self._update_tui(tui, current, "running")
            if not quiet:
                print(f"[Loom] Running node: {current}", flush=True)

            # Run node
            node = self._create_node(current)
            success, output, new_state = await node.run(shared_state)
            shared_state = new_state
            shared_state[f"{current}_output"] = output

            if not quiet:
                print(f"[Loom] Node {current}: {'PASS' if success else 'FAIL'}", flush=True)
            self._update_tui(tui, current, "completed" if success else "failed", output)

            # Persist and route
            state = PipelineState(
                current_node=current,
                visit_counts=visit_counts,
                shared_state=shared_state,
            )
            await self._persist_state(state)

            next_node = node.route(success)
            if not next_node:
                break
            current = next_node

        return state
