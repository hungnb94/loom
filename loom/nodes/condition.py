from typing import Any

import ast
import operator
from loom.nodes.base import BaseNode


# Whitelist of safe operators for restricted expression evaluation
_SAFE_OPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.And: operator.and_,
    ast.Or: operator.or_,
    ast.In: operator.contains,
    ast.Is: operator.is_,
    ast.Not: operator.not_,
}


class _SafeEvalError(Exception):
    """Raised when an expression contains unsafe AST nodes."""


class ConditionNode(BaseNode):
    """Evaluate a Jinja2-rendered Python expression safely.

    The expression is rendered with state variables, then evaluated with
    ast.literal_eval for simple values, or a restricted AST walker for
    comparisons and arithmetic — no raw eval() is used.
    """

    async def run(self, state: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        rendered = self.render(self.config.get("expression", ""), state)
        try:
            # Try literal_eval first for simple values (True, False, numbers, strings)
            result = ast.literal_eval(rendered.strip())
        except (ValueError, SyntaxError):
            # Fallback: restricted AST evaluation — no eval() call
            try:
                result = self._safe_eval(rendered.strip())
            except _SafeEvalError:
                result = False
        return bool(result), str(result), state

    @classmethod
    def _safe_eval(cls, expr: str):
        """Evaluate a simple expression using only whitelisted AST nodes."""
        tree = ast.parse(expr, mode="eval")
        return cls._eval_node(tree.body)

    @classmethod
    def _eval_node(cls, node: ast.AST):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in ("True", "False", "None"):
                return {"True": True, "False": False, "None": None}[node.id]
            raise _SafeEvalError(f"Unknown name: {node.id}")
        if isinstance(node, ast.UnaryOp):
            op = _SAFE_OPS.get(type(node.op))
            if not op:
                raise _SafeEvalError(f"Unsupported unary op: {type(node.op).__name__}")
            return op(cls._eval_node(node.operand))
        if isinstance(node, ast.BinOp):
            op = _SAFE_OPS.get(type(node.op))
            if not op:
                raise _SafeEvalError(f"Unsupported binary op: {type(node.op).__name__}")
            return op(cls._eval_node(node.left), cls._eval_node(node.right))
        if isinstance(node, ast.BoolOp):
            values = [cls._eval_node(v) for v in node.values]
            op = _SAFE_OPS.get(type(node.op))
            if not op:
                raise _SafeEvalError(f"Unsupported bool op: {type(node.op).__name__}")
            # Fold left-to-right for any number of values
            result = values[0]
            for v in values[1:]:
                result = op(result, v)
            return result
        if isinstance(node, ast.Compare):
            left = cls._eval_node(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                op_func = _SAFE_OPS.get(type(op))
                if not op_func:
                    raise _SafeEvalError(f"Unsupported compare op: {type(op).__name__}")
                right = cls._eval_node(comparator)
                if isinstance(op, ast.In):
                    left, right = right, left  # operator.contains(a, b) == b in a
                if not op_func(left, right):
                    return False
                left = right
            return True
        if isinstance(node, ast.Expression):
            return cls._eval_node(node.body)
        raise _SafeEvalError(f"Unsupported node type: {type(node).__name__}")

    def route(self, success: bool) -> str | None:
        if success:
            return self.config.get("on_true") or self.config.get("next")
        else:
            return self.config.get("on_false") or self.config.get("next")
