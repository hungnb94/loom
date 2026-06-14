from typing import Any

import asyncio
from loom.nodes.base import BaseNode


class ParallelNode(BaseNode):
    """Run multiple branches concurrently, aggregate outputs into shared_state.

    Succeeds only if ALL branches pass. Each branch's output is stored as
    ``{branch_name}_output`` in the shared state.
    """

    async def run(self, state: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        # Late import to break circular dependency (registry → parallel → registry)
        from loom.registry import NODE_REGISTRY

        branches = self.config.get("branches", [])
        if not branches:
            return True, "No branches to run", state

        nodes = []
        for branch in branches:
            node_class = NODE_REGISTRY.get(branch["type"])
            if not node_class:
                return False, f"Unknown branch type: {branch['type']}", state
            nodes.append(node_class(name=branch["name"], config=branch))

        # Run all branches concurrently
        results = await asyncio.gather(
            *[node.run(dict(state)) for node in nodes],
            return_exceptions=True,
        )

        all_passed = True
        outputs: list[str] = []
        updated_state = dict(state)

        for branch, result in zip(branches, results):
            name = branch["name"]
            output_key = f"{name}_output"
            if isinstance(result, BaseException):
                all_passed = False
                outputs.append(f"{name}: ERROR — {result}")
                updated_state[output_key] = str(result)
                continue
            success, output, branch_state = result
            if not success:
                all_passed = False
            outputs.append(f"{name}: {'PASS' if success else 'FAIL'} — {output[:200]}")
            updated_state[output_key] = output
            for key, value in branch_state.items():
                if key == output_key:
                    # Branch's own output always wins
                    updated_state[key] = value
                elif key not in updated_state:
                    # First-write wins for shared keys (concurrent branches
                    # each get a copy of parent state, so conflicts are rare)
                    updated_state[key] = value

        return all_passed, "\n".join(outputs), updated_state
