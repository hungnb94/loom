import os
from loom.nodes.base import BaseNode


class HumanNode(BaseNode):
    """Pause pipeline for human approval.

    Behavior:
    - _user_input set → use it directly (test mode)
    - Non-TTY stdin (CI/pipe) → default "approve"
    - TTY stdin → prompt user interactively
    """

    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self._user_input: str | None = None

    async def run(self, state: dict) -> tuple[bool, str, dict]:
        if self._user_input is None:
            if not os.isatty(0):
                self._user_input = "approve"
            else:
                try:
                    self._user_input = input(f"[{self.name}] approve/decline? ")
                except (EOFError, KeyboardInterrupt):
                    self._user_input = "decline"

        success = self._user_input.lower() in ("approve", "yes", "y")
        return success, self._user_input, state

    def route(self, success: bool) -> str | None:
        if success:
            return self.config.get("on_approve") or self.config.get("next")
        else:
            return self.config.get("on_decline") or self.config.get("on_skip") or self.config.get("next")
