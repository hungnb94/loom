import asyncio
from concurrent.futures import ThreadPoolExecutor
from loom.nodes.base import BaseNode


class ParallelDispatcher:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers

    async def run(self, nodes: list[BaseNode], state: dict) -> dict[str, tuple]:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {
                node.name: loop.run_in_executor(pool, self._run_node, node, state)
                for node in nodes
            }
            results = {}
            for name, future in futures.items():
                results[name] = await future
            return results

    def _run_node(self, node: BaseNode, state: dict) -> tuple:
        # Run async node in sync context for thread pool
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(node.run(state))
        finally:
            loop.close()
