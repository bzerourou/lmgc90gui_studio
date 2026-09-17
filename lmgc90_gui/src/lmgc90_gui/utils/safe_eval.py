"""Restricted expression evaluator (AST) for numeric fields and dynamic variables."""
from __future__ import annotations

import ast
import math
import operator
from typing import Any

_BIN = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg, ast.Not: operator.not_}
_CMP = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
}
_ALLOWED_FUNCS = {
    "pi": math.pi,
    "e": math.e,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "sum": sum,
    "len": len,
    "list": list,
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
}


class SafeEvaluator:
    def __init__(self, allowed_names: dict[str, Any] | None = None):
        self.allowed_names = {**_ALLOWED_FUNCS, **(allowed_names or {})}

    def eval_expression(self, expr: str) -> Any:
        tree = ast.parse(expr, mode="eval")
        return _eval(tree.body, self.allowed_names)


def safe_eval(expr: str, context: dict[str, Any] | None = None) -> Any:
    return SafeEvaluator(context).eval_expression(expr)


def _eval(node: ast.AST, ctx: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id not in ctx:
            raise NameError(node.id)
        return ctx[node.id]
    if isinstance(node, ast.BinOp):
        op = _BIN.get(type(node.op))
        if op is None:
            raise ValueError(f"Opération non autorisée : {type(node.op).__name__}")
        return op(_eval(node.left, ctx), _eval(node.right, ctx))
    if isinstance(node, ast.UnaryOp):
        op = _UNARY.get(type(node.op))
        if op is None:
            raise ValueError(f"Opération non autorisée : {type(node.op).__name__}")
        return op(_eval(node.operand, ctx))
    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            val = True
            for v in node.values:
                val = _eval(v, ctx)
                if not val:
                    return val
            return val
        if isinstance(node.op, ast.Or):
            val = False
            for v in node.values:
                val = _eval(v, ctx)
                if val:
                    return val
            return val
        raise ValueError("Opération non autorisée : BoolOp")
    if isinstance(node, ast.Compare):
        left = _eval(node.left, ctx)
        for op_node, comp in zip(node.ops, node.comparators):
            op = _CMP.get(type(op_node))
            if op is None:
                raise ValueError(f"Opération non autorisée : {type(op_node).__name__}")
            right = _eval(comp, ctx)
            if not op(left, right):
                return False
            left = right
        return True
    if isinstance(node, ast.IfExp):
        return _eval(node.body, ctx) if _eval(node.test, ctx) else _eval(node.orelse, ctx)
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id not in ctx:
                raise ValueError(f"fonction non autorisée : {node.func.id}")
            fn = ctx[node.func.id]
        elif isinstance(node.func, ast.Attribute):
            obj = _eval(node.func.value, ctx)
            fn = getattr(obj, node.func.attr)
        else:
            raise ValueError("Opération non autorisée : Call")
        args = [_eval(a, ctx) for a in node.args]
        kwargs = {kw.arg: _eval(kw.value, ctx) for kw in node.keywords if kw.arg}
        return fn(*args, **kwargs)
    if isinstance(node, ast.Attribute):
        if node.attr.startswith("_"):
            raise ValueError("Opération non autorisée : private attr")
        obj = _eval(node.value, ctx)
        return getattr(obj, node.attr)
    if isinstance(node, ast.Subscript):
        obj = _eval(node.value, ctx)
        key = _eval(node.slice, ctx)
        return obj[key]
    if isinstance(node, ast.List):
        return [_eval(e, ctx) for e in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_eval(e, ctx) for e in node.elts)
    if isinstance(node, ast.Dict):
        return {
            _eval(k, ctx): _eval(v, ctx)
            for k, v in zip(node.keys, node.values)
            if k is not None
        }
    if isinstance(node, ast.ListComp):
        return _eval_listcomp(node, ctx)
    if isinstance(node, ast.GeneratorExp):
        return list(_eval_listcomp(node, ctx))  # type: ignore[arg-type]
    raise ValueError(f"Opération non autorisée : {type(node).__name__}")


def _eval_listcomp(node: ast.ListComp | ast.GeneratorExp, ctx: dict[str, Any]) -> list:
    if len(node.generators) != 1:
        raise ValueError("une seule clause for autorisée dans les compréhensions")
    gen = node.generators[0]
    iterable = _eval(gen.iter, ctx)
    if not isinstance(gen.target, ast.Name):
        raise ValueError("cible de for simple uniquement")
    name = gen.target.id
    out = []
    for item in iterable:
        local = {**ctx, name: item}
        if all(_eval(c, local) for c in gen.ifs):
            out.append(_eval(node.elt, local))
    return out
