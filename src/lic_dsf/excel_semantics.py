"""Version-specific Excel resolver and error semantics for the pinned evaluator.

Copyright (c) 2026 Teal Insights. Distributed under the MIT License.
Numerical operations are preserved from the licensed compatibility implementation.
"""
from __future__ import annotations
from typing import Any, Callable
_applied = False

def apply() -> None:
    global _applied
    if _applied:
        return
    from excel_grapher.core.formula_ast import BinaryOpNode, UnaryOpNode
    from excel_grapher.grapher import resolver
    original = resolver._eval_number_for_defined_name

    def patched(node: Any, get_cell_value: Callable[[str], Any], bounds: dict[str, tuple[int, int]]) -> int | float | None:
        if isinstance(node, BinaryOpNode):
            left = patched(node.left, get_cell_value, bounds)
            right = patched(node.right, get_cell_value, bounds)
            if left is None or right is None:
                return None
            try:
                if node.op == '+':
                    out = left + right
                elif node.op == '-':
                    out = left - right
                elif node.op == '*':
                    out = left * right
                elif node.op == '/':
                    out = left / right
                else:
                    return None
            except ZeroDivisionError:
                return None
            return int(out) if out == int(out) else out
        if isinstance(node, UnaryOpNode):
            operand = patched(node.operand, get_cell_value, bounds)
            if operand is None:
                return None
            if node.op == '-':
                return -operand
            if node.op == '+':
                return operand
            return None
        return original(node, get_cell_value, bounds)
    resolver._eval_number_for_defined_name = patched
    _apply_error_semantics_patches()
    _applied = True

def _apply_error_semantics_patches() -> None:
    import numpy as np
    from excel_grapher.core import operators as _ops
    from excel_grapher.core.coercions import to_number as _orig_to_number
    from excel_grapher.core.types import CellValue, XlError
    from excel_grapher.evaluator import evaluator as _ev
    from excel_grapher.evaluator import functions as _fns
    _ev._SKIP_ERROR_PRECHECK.update({'ISNUMBER', 'ISTEXT'})
    _fns.FUNCTIONS['ISTEXT'] = lambda v: isinstance(v, str) and (not isinstance(v, XlError))

    def _to_number_no_empty_text(value: CellValue) -> float | XlError:
        if isinstance(value, str) and value.strip() == '':
            return XlError.VALUE
        return _orig_to_number(value)
    _ops.to_number = _to_number_no_empty_text
    _ev.to_number = _to_number_no_empty_text
    _NUMERIC = (int, float, np.integer, np.floating)

    def _faithful_numbers(args: tuple[Any, ...]) -> list[float] | XlError:
        nums: list[float] = []
        for a in args:
            if isinstance(a, (np.ndarray, list, tuple)):
                stack = [a]
                while stack:
                    seq = stack.pop()
                    it = seq.flat if isinstance(seq, np.ndarray) else seq
                    for v in it:
                        if isinstance(v, (np.ndarray, list, tuple)):
                            stack.append(v)
                        elif isinstance(v, XlError):
                            return v
                        elif isinstance(v, bool) or v is None or isinstance(v, str):
                            continue
                        elif isinstance(v, _NUMERIC):
                            nums.append(float(v))
                continue
            n = _to_number_no_empty_text(a)
            if isinstance(n, XlError):
                return n
            nums.append(float(n))
        return nums

    def _make_reducer(reduce: Callable[[list[float]], 'CellValue'], empty: 'CellValue') -> Callable[..., 'CellValue']:

        def fn(*args: Any) -> CellValue:
            nums = _faithful_numbers(args)
            if isinstance(nums, XlError):
                return nums
            if not nums:
                return empty
            return reduce(nums)
        return fn

    def _stdev(nums: list[float]) -> CellValue:
        if len(nums) < 2:
            return XlError.DIV
        mean = sum(nums) / len(nums)
        return (sum(((x - mean) ** 2 for x in nums)) / (len(nums) - 1)) ** 0.5
    _fns.FUNCTIONS['SUM'] = _make_reducer(lambda ns: float(sum(ns)), 0.0)
    _fns.FUNCTIONS['AVERAGE'] = _make_reducer(lambda ns: float(sum(ns) / len(ns)), XlError.DIV)
    _fns.FUNCTIONS['MIN'] = _make_reducer(lambda ns: float(min(ns)), 0.0)
    _fns.FUNCTIONS['MAX'] = _make_reducer(lambda ns: float(max(ns)), 0.0)
    _fns.FUNCTIONS['STDEV'] = _make_reducer(_stdev, XlError.DIV)
    from excel_grapher.core.types import ExcelRange
    _orig_rbo = _ev.FormulaEvaluator._resolve_binary_operand

    def _rbo_scalar_1x1(self: Any, value: Any) -> Any:
        if isinstance(value, ExcelRange) and value.start_row == value.end_row and (value.start_col == value.end_col):
            return self._auto_resolve_single_cell(value)
        return _orig_rbo(self, value)
    _ev.FormulaEvaluator._resolve_binary_operand = _rbo_scalar_1x1
