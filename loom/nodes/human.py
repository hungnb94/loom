from loom.nodes.base import BaseNode


class HumanNode(BaseNode):
    """A node that pauses for human input (approve/decline).

    In production this would block on TUI input. For testing, _user_input
    can be set directly.
    """

    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self._user_input: str | None = None

    async def run(self, state: dict):
        if self._user_input is None:
            # Default to "approve" so tests don't hang
            self._user_input = "approve"
        success = self._user_input in ("approve", "yes", "y")
        return success, self._user_input, state

    def route(self, success: bool) -> str | None:
        if success:
            return self.config.get("on_approve") or self.config.get("next")
        else:
            return self.config.get("on_decline") or self.config.get("on_skip") or self.config.get("next")
