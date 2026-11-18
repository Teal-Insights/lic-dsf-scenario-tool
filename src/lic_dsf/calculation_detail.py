"""Local diagnostic for an unexpected calculation failure.

The stable intake code stays the failure identity. This module adds the engine
exception and, when that exception names a generated input, the worksheet cell
from the library's cell map. Tracebacks and filesystem paths are omitted.
"""
from __future__ import annotations

import ast
import re
from collections.abc import Mapping

_SUFFIXES = (" out of domain:", " has type ", " value ")
_STABLE_CODE = re.compile(r"[a-z0-9_]{1,200}")
_DETAIL = re.compile(
    r"^(?P<kind>[A-Za-z_][A-Za-z0-9_]*)"
    r"(?: at (?P<sheet>[^!\\/\r\n:?*[\]]{1,120})!(?P<cell>[A-Z]{1,3}[1-9][0-9]{0,6}))?"
    r": (?P<message>\S.*)$"
)
_QUOTED_ADDRESS = re.compile(r"^'((?:[^']|'')*)'!([A-Z]{1,3}[1-9][0-9]{0,6})$")
_PLAIN_ADDRESS = re.compile(r"^([A-Za-z0-9_]{1,80})!([A-Z]{1,3}[1-9][0-9]{0,6})$")
_MAX_DETAIL = 1000
_CATALOG = None


def failure_job(exc, scenario_id):
    """Job record for a failed calculation. The detail is separate from the stable sentence."""
    from .store import StaleResult
    text = str(exc)
    if (isinstance(exc, (ValueError, StaleResult)) and len(text) < 400
            and "/" not in text and "\\" not in text):
        message = text
    else:
        message = "Calculation could not finish. The saved scenario is retained."
    finished = {"status": "failed", "message": message, "scenario_id": scenario_id}
    detail = public_detail(getattr(exc, "detail", None))
    if not detail:
        candidate = failure_detail(exc)
        if candidate:
            head, _separator, body = candidate.partition(": ")
            # A cell name is new information. So is an engine message that the
            # stable sentence replaced. The sentence itself is not repeated.
            if " at " in head or body != message:
                detail = candidate
    if detail:
        finished["detail"] = detail
    return finished


def failure_detail(exc):
    """Exception type, message, and worksheet cell. None when the text is not safe to show."""
    origin = _origin(exc)
    if origin is None:
        return None
    message = _safe_message(origin)
    if message is None or _STABLE_CODE.fullmatch(message):
        return None
    kind = type(origin).__name__
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", kind):
        kind = "Error"
    address = _address_for(message)
    if address:
        text = f"{kind} at {address}: {message}"
    else:
        text = f"{kind}: {message}"
    if len(text) > _MAX_DETAIL:
        text = text[:_MAX_DETAIL - 3].rstrip() + "..."
    return public_detail(text)


def public_detail(value):
    """Return a diagnostic that names no filesystem path, or None."""
    if not isinstance(value, str) or not value or len(value) > _MAX_DETAIL:
        return None
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        return None
    if "\\" in value or "/" in value or "://" in value or "../" in value:
        return None
    match = _DETAIL.fullmatch(value)
    if not match:
        return None
    sheet = match.group("sheet")
    if sheet is not None and sheet.strip() != sheet:
        return None
    return value


def _origin(exc):
    chosen = None
    for item in _chain(exc):
        message = _safe_message(item)
        if not message or _STABLE_CODE.fullmatch(message):
            continue
        if _address_for(message):
            return item
        if chosen is None:
            chosen = item
    return chosen


def _chain(exc):
    seen = set()
    current = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        yield current
        current = current.__cause__


def _safe_message(exc):
    try:
        text = str(exc)
    except Exception:
        return None
    if not isinstance(text, str) or not text or len(text) > 4000:
        return None
    if any(ord(char) < 32 or ord(char) == 127 for char in text):
        return None
    if "\\" in text or "/" in text or "://" in text or "../" in text:
        return None
    return text


def _catalog():
    global _CATALOG
    if _CATALOG is None:
        from lic_dsf_2025_08_12 import data
        catalog = {}
        for name, value in vars(data).items():
            if isinstance(name, str) and name.endswith("_CELLS") and isinstance(value, Mapping):
                catalog.setdefault(name[:-len("_CELLS")].lower(), value)
            series_id = getattr(getattr(value, "schema", None), "series_id", None)
            cells = getattr(value, "cells", None)
            if isinstance(series_id, str) and series_id and isinstance(cells, Mapping):
                catalog.setdefault(series_id, cells)
        _CATALOG = catalog
    return _CATALOG


def _address_for(message):
    series_id = _series_id(message)
    if not series_id:
        return None
    rest = message[len(series_id):]
    if rest.startswith("["):
        return None
    if rest.startswith("("):
        _coordinate, rest = _take_tuple(rest)
        if _coordinate is None:
            return None
        coordinate = _coordinate
    else:
        coordinate = ()
    if not any(rest.startswith(suffix) for suffix in _SUFFIXES):
        return None
    cells = _catalog().get(series_id)
    if cells is None:
        return None
    try:
        raw = cells.get(coordinate)
    except Exception:
        return None
    return _display_address(raw)


def _series_id(message):
    best = None
    for series_id in _catalog():
        if len(series_id) <= len(best or ""):
            continue
        if not message.startswith(series_id):
            continue
        rest = message[len(series_id):]
        if rest[:1] in (" ", "(", "["):
            best = series_id
    return best


def _take_tuple(text):
    depth = 0
    quote = None
    escaped = False
    for index, char in enumerate(text):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                literal = text[:index + 1]
                try:
                    value = ast.literal_eval(literal)
                except (SyntaxError, ValueError):
                    return None, text
                if type(value) is not tuple or any(type(part) not in (str, int) for part in value):
                    return None, text
                return value, text[index + 1:]
    return None, text


def _display_address(raw):
    if not isinstance(raw, str):
        return None
    quoted = _QUOTED_ADDRESS.fullmatch(raw)
    if quoted:
        sheet = quoted.group(1).replace("''", "'")
        cell = quoted.group(2)
    else:
        plain = _PLAIN_ADDRESS.fullmatch(raw)
        if not plain:
            return None
        sheet, cell = plain.group(1), plain.group(2)
    if not sheet or any(char in sheet for char in "\\/:?*[]"):
        return None
    shown = f"{sheet}!{cell}"
    if len(shown) > 160:
        return None
    return shown
