"""Calculation loads workbook inputs through the generated library."""
import ast
import unittest
from pathlib import Path

import lic_dsf.engine as engine


def _index(tree):
    functions = {}
    classes = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            functions[node.name] = node
        elif isinstance(node, ast.ClassDef):
            classes[node.name] = node
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    functions[f"{node.name}.{item.name}"] = item
    return functions, classes


def _imports_model(fn):
    for node in ast.walk(fn):
        if isinstance(node, ast.ImportFrom) and node.module == "lic_dsf_2025_08_12":
            if any(alias.name == "Model" for alias in node.names):
                return True
        if isinstance(node, ast.Import):
            if any(alias.name == "lic_dsf_2025_08_12" for alias in node.names):
                return True
    return False


def _calls_model_from_workbook(fn):
    for node in ast.walk(fn):
        call = node.func if isinstance(node, ast.Call) else None
        if not isinstance(call, ast.Attribute) or call.attr != "from_workbook":
            continue
        value = call.value
        if isinstance(value, ast.Name) and value.id == "Model":
            return True
        if isinstance(value, ast.Attribute) and value.attr == "Model":
            return True
    return False


def _reachable(functions, classes, start):
    seen = set()

    def walk(name):
        if name in seen or name not in functions:
            return
        seen.add(name)
        for node in ast.walk(functions[name]):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                called = node.func.id
                if called in classes:
                    walk(f"{called}.__init__")
                walk(called)

    walk(start)
    return seen


class ModelFromWorkbook(unittest.TestCase):
    maxDiff = None

    def test_calculation_loads_inputs_with_model_from_workbook(self):
        source = Path(engine.__file__).read_text(encoding="utf-8")
        functions, classes = _index(ast.parse(source))
        self.assertIn("_calculate", functions)
        reached = _reachable(functions, classes, "_calculate")
        importers = sorted(name for name in reached if _imports_model(functions[name]))
        callers = sorted(name for name in reached if _calls_model_from_workbook(functions[name]))
        self.assertTrue(
            importers,
            "calculation must import Model from lic_dsf_2025_08_12; "
            f"reached {sorted(reached)}",
        )
        self.assertTrue(
            callers,
            "calculation must call Model.from_workbook; "
            f"reached {sorted(reached)}",
        )


if __name__ == "__main__":
    unittest.main()
