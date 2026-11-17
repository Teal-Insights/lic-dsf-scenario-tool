"""Use a workbook's own classification and indicator rows during calculation.

The pinned library stores the template's classification, CPIA, remittance and
GDP rows as constants. A supported workbook can carry a different country in
those same cells. Calculation reads the workbook row when it differs, then
restores the template constants. An unchanged row stays on the snapshot, so a
template workbook is not given a second copy of the same values.
"""
from __future__ import annotations

import dataclasses
from contextlib import contextmanager
from pathlib import Path

_PREFIXES = ("CLASSIFICATION_", "CPIA_", "DATA_GDPUSD_", "DATA_REM_")


def _widen(schema):
    types = tuple(dict.fromkeys((*schema.value_types, int, float, str, type(None))))
    return dataclasses.replace(schema, value_types=types)


def _series_row(book, binding, read_cell, snapshot_cells, tensor_type):
    records = [(coord, read_cell(book, address)) for coord, address in snapshot_cells(binding).items()]
    if dict(binding.items()) == dict(records):
        return None
    tensor = tensor_type.from_records(domain=binding.domain, records=records)
    return type(binding)(tensor.domain, tensor._values, schema=_widen(binding.schema), cells=binding.cells)


def _scalar_row(book, data_module, name, binding, read_cell, scalar_address):
    cells = getattr(data_module, f"{name}_CELLS", None)
    if cells is None or isinstance(binding, type) or getattr(binding, "domain", None) is not None:
        return None
    value = read_cell(book, scalar_address(cells))
    if value == binding:
        return None
    return value


def _apply(path, saved):
    import lic_dsf_2025_08_12.data as data
    from fastpyxl import load_workbook
    from lic_dsf_2025_08_12.tensor import Tensor
    from lic_dsf_2025_08_12.workbook import _read_cell, _scalar_address, _snapshot_cells

    book = load_workbook(path, data_only=True, keep_vba=path.suffix.lower() == ".xlsm")
    try:
        for name in dir(data):
            if not name.startswith(_PREFIXES) or name.endswith(("_CELLS", "_DOMAIN")):
                continue
            binding = getattr(data, name)
            if getattr(binding, "cells", None) is not None and getattr(binding, "domain", None) is not None:
                replacement = _series_row(book, binding, _read_cell, _snapshot_cells, Tensor)
            else:
                replacement = _scalar_row(book, data, name, binding, _read_cell, _scalar_address)
            if replacement is None:
                continue
            saved[name] = binding
            setattr(data, name, replacement)
    finally:
        book.close()


@contextmanager
def workbook_rows(path):
    """Install differing baked rows from `path` for the body of the block."""
    saved = {}
    try:
        _apply(Path(path), saved)
        yield
    finally:
        if saved:
            import lic_dsf_2025_08_12.data as data
            for name, binding in saved.items():
                setattr(data, name, binding)
