import asyncio
from loom.nodes.base import BaseNode


class ParallelDispatcher:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers

    async def run(self, nodes: list[BaseNode], state: dict) -> dict[str, tuple]:
        semaphore = asyncio.Semaphore(self.max_workers)

        async def _run_with_limit(node: BaseNode) -> tuple[str, tuple]:
            async with semaphore:
                result = await node.run(state)
                return node.name, result

        tasks = [_run_with_limit(node) for node in nodes]
        results = await asyncio.gather(*tasks)
        return {name: result for name, result in results}
