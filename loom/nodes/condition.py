from jinja2 import Template

from loom.nodes.base import BaseNode


class ConditionNode(BaseNode):
    """A node that evaluates a Jinja2-rendered Python expression.

    The expression is first rendered with Jinja2 (substituting state variables),
    then evaluated with Python eval(). This lets pipeline authors write
    conditions like ``{{x}} > 5`` or ``{{status}} == "ready"``.
    """

    async def run(self, state: dict):
        expression = self.config.get("expression", "")
        template = Template(expression)
        rendered = template.render(**state)
        try:
            result = eval(rendered)  # noqa: S307 — deliberate: controlled pipeline expressions
        except Exception:
            result = False
        return bool(result), str(result), state

    def route(self, success: bool) -> str | None:
        if success:
            return self.config.get("on_true") or self.config.get("next")
        else:
            return self.config.get("on_false") or self.config.get("next")
