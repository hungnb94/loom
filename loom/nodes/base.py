from typing import Any


class BaseNode:
    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config

    async def run(self, state: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        """Return (success, output, updated_state).

        Subclasses must override this method.
        """
        raise NotImplementedError(
            f"Node '{self.name}' must implement run()"
        )

    def route(self, success: bool) -> str | None:
        if success:
            return self.config.get("on_pass") or self.config.get("next")
        else:
            return self.config.get("on_fail") or self.config.get("next")
