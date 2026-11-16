"""Acceptance gate: this project does not import excel-grapher.

The calculation backend is the generated ``lic_dsf_2025_08_12`` library.
Importing ``excel_grapher``, or declaring the ``excel-grapher`` distribution,
keeps this check failed.
"""
import ast
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOTS = ("src", "tests", "scripts", "packaging")
MODULE = "excel_grapher"
DISTRIBUTION = "excel-grapher"


def _is_grapher(name: str) -> bool:
    return name == MODULE or name.startswith(MODULE + ".") or name == DISTRIBUTION


def _imported(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _is_grapher(alias.name):
                    found.append(f"{path.relative_to(ROOT)}:{node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module and _is_grapher(node.module):
            found.append(f"{path.relative_to(ROOT)}:{node.lineno}: from {node.module} import ...")
        elif isinstance(node, ast.Call) and node.args and isinstance(node.args[0], ast.Constant):
            target = node.args[0].value
            attr = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
            if attr in {"import_module", "__import__"} and isinstance(target, str) and _is_grapher(target):
                found.append(f"{path.relative_to(ROOT)}:{node.lineno}: {attr}({target!r})")
    return found


def _python_files():
    for name in PYTHON_ROOTS:
        base = ROOT / name
        if base.is_dir():
            yield from sorted(path for path in base.rglob("*.py") if "__pycache__" not in path.parts)


def _declared_dependencies() -> list[str]:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8")).get("project", {})
    specs = list(project.get("dependencies", []))
    for group in project.get("optional-dependencies", {}).values():
        specs.extend(group)
    offenders = []
    for spec in specs:
        name = spec.split("@", 1)[0].split("[", 1)[0].strip().lower().replace("_", "-")
        if name == DISTRIBUTION:
            offenders.append(spec)
    return offenders


class NoExcelGrapher(unittest.TestCase):
    maxDiff = None

    def test_sources_do_not_import_excel_grapher(self):
        imports = [item for path in _python_files() for item in _imported(path)]
        self.assertEqual(imports, [])

    def test_project_does_not_depend_on_excel_grapher(self):
        self.assertEqual(_declared_dependencies(), [])


if __name__ == "__main__":
    unittest.main()
