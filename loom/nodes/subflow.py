from loom.nodes.base import BaseNode


class SubflowNode(BaseNode):
    """A node that runs a sub-pipeline (pipeline-within-a-pipeline).

    In production this would spawn a new GraphExecutor for the referenced
    pipeline file. For V1 it returns success immediately as a stub.
    """

    async def run(self, state: dict) -> tuple[bool, str, dict]:
        pipeline_path = self.config.get("pipeline")
        if not pipeline_path:
            return False, "No pipeline specified", state
        # In real implementation, this would spawn a new executor
        return True, f"Subflow {pipeline_path} completed", state

    def route(self, success: bool) -> str | None:
        if success:
            return self.config.get("on_complete") or self.config.get("next")
        else:
            return self.config.get("on_error") or self.config.get("next")
