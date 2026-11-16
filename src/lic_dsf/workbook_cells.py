"""Copy a workbook and edit selected cells.

The original file is not modified. ``apply_number_cells`` replaces a cell
with a numeric literal. ``refresh_cached_numbers`` changes a cached result
and leaves its formula in place. Scenario adjustments use the literal
replacement so they reach ``Model.from_workbook`` without resaving the
analyst's workbook.
"""
from __future__ import annotations

from pathlib import Path
import re
import zipfile
from xml.etree import ElementTree as ET

from .workbooks import IntakeError

_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_CELL = re.compile(
    r'<c\b(?P<pre>[^>]*?)\sr="(?P<addr>[A-Z]+[0-9]+)"(?P<post>[^>]*?)(?P<close>/>|>(?P<body>.*?)</c>)',
    re.DOTALL,
)
_CACHED_NUMBER = re.compile(
    r"<v>(-?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)</v>"
)


def refresh_cached_numbers(source, dest, edits):
    """Replace cached numeric results in a copy. Formulas stay in place.

    ``edits`` maps a sheet name to ``{address: number}``. This is how a saved
    workbook carries a recalculated year header without dropping the formula
    the generated library uses to recognise that header. A missing sheet,
    cell, or cached number raises ``IntakeError``.
    """
    _write_copy(source, dest, edits, _refresh_numbers)


def apply_number_cells(source, dest, edits):
    """Write ``edits`` into a copy of ``source``.

    ``edits`` maps a sheet name to ``{address: number}``. Missing sheets or
    cells raise ``IntakeError``.
    """
    _write_copy(source, dest, edits, _set_numbers)


def _write_copy(source, dest, edits, rewrite):
    source = Path(source)
    dest = Path(dest)
    with zipfile.ZipFile(source) as book:
        targets = _sheet_targets(book)
        replaced = {}
        for sheet, cells in edits.items():
            if sheet not in targets:
                raise IntakeError("input_target_missing_from_workbook")
            member = targets[sheet]
            text = book.read(member).decode("utf-8")
            replaced[member] = rewrite(text, cells).encode("utf-8")
        with zipfile.ZipFile(dest, "w") as out:
            for info in book.infolist():
                payload = replaced.get(info.filename)
                if payload is None:
                    payload = book.read(info.filename)
                out.writestr(info, payload)


def _sheet_targets(book):
    workbook = ET.fromstring(book.read("xl/workbook.xml"))
    relationships = ET.fromstring(book.read("xl/_rels/workbook.xml.rels"))
    targets = {item.attrib["Id"]: item.attrib["Target"] for item in relationships}
    names = {}
    for sheet in workbook.findall(f"{{{_MAIN}}}sheets/{{{_MAIN}}}sheet"):
        name = sheet.attrib["name"]
        target = targets[sheet.attrib[f"{{{_REL}}}id"]]
        if target.startswith("/"):
            member = target.lstrip("/")
        elif target.startswith("xl/"):
            member = target
        else:
            member = "xl/" + target
        names[name] = member
    return names


def _set_numbers(xml, cells):
    pending = {str(address): float(value) for address, value in cells.items()}
    found = set()

    def replace(match):
        address = match.group("addr")
        if address not in pending:
            return match.group(0)
        found.add(address)
        pre = re.sub(r'\s+t="[^"]*"', "", match.group("pre"))
        post = re.sub(r'\s+t="[^"]*"', "", match.group("post"))
        number = format(pending[address], ".16g")
        return f'<c{pre} r="{address}"{post}><v>{number}</v></c>'

    updated = _CELL.sub(replace, xml)
    missing = sorted(set(pending) - found)
    if missing:
        raise IntakeError("input_target_missing_from_workbook")
    return updated


def _refresh_numbers(xml, cells):
    pending = {str(address): float(value) for address, value in cells.items()}
    found = set()

    def replace(match):
        address = match.group("addr")
        if address not in pending:
            return match.group(0)
        body = match.group("body")
        if body is None or _CACHED_NUMBER.search(body) is None:
            return match.group(0)
        found.add(address)
        number = format(pending[address], ".16g")
        body = _CACHED_NUMBER.sub(f"<v>{number}</v>", body, count=1)
        return f'<c{match.group("pre")} r="{address}"{match.group("post")}>{body}</c>'

    updated = _CELL.sub(replace, xml)
    missing = sorted(set(pending) - found)
    if missing:
        raise IntakeError("input_target_missing_from_workbook")
    return updated
