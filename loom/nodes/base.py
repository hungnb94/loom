from typing import Any
from jinja2 import Template


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

    @staticmethod
    def render(template_str: str, state: dict[str, Any]) -> str:
        """Render a Jinja2 template with shared state."""
        return Template(template_str).render(**state)
