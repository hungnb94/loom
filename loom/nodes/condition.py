from loom.nodes.base import BaseNode


class ConditionNode(BaseNode):
    """Evaluate a Jinja2-rendered Python expression.

    The expression is rendered with state variables, then evaluated with eval().
    """

    async def run(self, state: dict) -> tuple[bool, str, dict]:
        rendered = self.render(self.config.get("expression", ""), state)
        try:
            result = eval(rendered)  # noqa: S307
        except Exception:
            result = False
        return bool(result), str(result), state

    def route(self, success: bool) -> str | None:
        if success:
            return self.config.get("on_true") or self.config.get("next")
        else:
            return self.config.get("on_false") or self.config.get("next")
