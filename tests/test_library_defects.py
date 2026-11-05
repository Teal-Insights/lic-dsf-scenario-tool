"""Correct behavior the pinned generated library does not implement yet.

These checks stay failed on lic-dsf-2025-08-12 121015367f8c. A later library
revision should make them pass. Do not weaken them, skip them, or retarget
them at the snapshot year to hide a defect.

The workbook is the public library test fixture for that revision. It is
downloaded when it is not already available. It is not committed here.
"""
import os
from pathlib import Path
import tempfile
import urllib.request
import unittest

from openpyxl import load_workbook

from lic_dsf.compare import ATOL, compare_one
from lic_dsf.ida21 import PUBLIC, EXTERNAL, cell
from lic_dsf.workbook_cells import apply_number_cells

PIN = "121015367f8ca6a6d9dab5fc94bfe9596605fd00"
FIXTURE_URL = (
    "https://github.com/Teal-Insights/lic-dsf-2025-08-12/raw/"
    f"{PIN}/tests/fixtures/workbook.xlsm"
)
GROWTH = "Real GDP growth (in percent)"
SHIFTED_YEAR = 2030


def _workbook():
    override = os.environ.get("DSF_TEST_WORKBOOK")
    if override:
        return Path(override)
    cached = Path(tempfile.gettempdir()) / f"lic-dsf-2025-08-12-{PIN}.xlsm"
    if cached.is_file() and cached.stat().st_size > 1_000_000:
        return cached
    urllib.request.urlretrieve(FIXTURE_URL, cached)
    return cached


def _cached(path, sheet, address):
    book = load_workbook(path, read_only=True, data_only=True, keep_links=False)
    try:
        return book[sheet][address].value
    finally:
        book.close()


class LibraryDefects(unittest.TestCase):
    maxDiff = None

    def test_unshifted_delta_cell_is_imported(self):
        """A value in the 2024 growth column is bound at 2024."""
        self.assertEqual(ATOL, 1e-6)
        source = _workbook()
        edits = {PUBLIC: {cell(5 + offset, 20): 0 for offset in range(21)}}
        edits[PUBLIC]["E20"] = 1.25
        with tempfile.TemporaryDirectory() as root:
            dest = Path(root) / "delta.xlsm"
            apply_number_cells(source, dest, edits)
            from lic_dsf_2025_08_12 import Model
            model = Model.from_workbook(dest)
            actual = model.customized_public_delta.sel(INDICATOR=GROWTH, TIME_PERIOD=2024)
            ok, reason = compare_one(1.25, actual)
            self.assertTrue(ok, f"expected 1.25 at 2024, got {actual!r} ({reason})")

    def test_changed_current_year_reads_the_first_projection_column(self):
        """Column E belongs to the workbook's current projection year."""
        self.assertEqual(ATOL, 1e-6)
        source = _workbook()
        edits = {"Input 1 - Basics": {"C17": SHIFTED_YEAR, "C18": SHIFTED_YEAR}, PUBLIC: {}}
        for offset in range(21):
            edits[PUBLIC][cell(5 + offset, 7)] = SHIFTED_YEAR + offset
            edits[PUBLIC][cell(5 + offset, 20)] = 0
        edits[PUBLIC]["E20"] = 1.25
        with tempfile.TemporaryDirectory() as root:
            dest = Path(root) / "shifted.xlsm"
            apply_number_cells(source, dest, edits)
            self.assertEqual(float(_cached(dest, "Input 1 - Basics", "C17")), float(SHIFTED_YEAR))
            self.assertEqual(float(_cached(dest, PUBLIC, "E20")), 1.25)
            from lic_dsf_2025_08_12 import Model
            model = Model.from_workbook(dest)
            actual = model.customized_public_delta.sel(INDICATOR=GROWTH, TIME_PERIOD=SHIFTED_YEAR)
            ok, reason = compare_one(1.25, actual)
            self.assertTrue(
                ok,
                f"projection year {SHIFTED_YEAR} should be the first-column delta 1.25, "
                f"got {actual!r} ({reason})",
            )

    def test_from_workbook_imports_financing_override_cells(self):
        """User-entered C21, C23 and C24 replace the formula defaults."""
        self.assertEqual(ATOL, 1e-6)
        source = _workbook()
        with tempfile.TemporaryDirectory() as root:
            dest = Path(root) / "overrides.xlsm"
            apply_number_cells(source, dest, {EXTERNAL: {"C21": 0.125, "C23": 7, "C24": 40}})
            self.assertEqual(float(_cached(dest, EXTERNAL, "C21")), 0.125)
            self.assertEqual(float(_cached(dest, EXTERNAL, "C23")), 7)
            self.assertEqual(float(_cached(dest, EXTERNAL, "C24")), 40)
            from lic_dsf_2025_08_12 import Model
            model = Model.from_workbook(dest)
            terms = model.custom_ext_average_interest_rate_new_debt_by_row
            expected = {
                "Average interest rate on new debt": 0.125,
                "Average grace period on new debt": 7,
                "Average maturity of new debt": 40,
            }
            for indicator, value in expected.items():
                actual = terms.sel(INDICATOR=indicator)
                ok, reason = compare_one(value, actual)
                self.assertTrue(ok, f"{indicator}: expected {value}, got {actual!r} ({reason})")

    def test_negative_growth_delta_is_accepted(self):
        """A lower-growth adjustment is a valid customized-scenario delta."""
        self.assertEqual(ATOL, 1e-6)
        source = _workbook()
        edits = {PUBLIC: {cell(5 + offset, 20): 0 for offset in range(21)}}
        edits[PUBLIC]["E20"] = -1
        with tempfile.TemporaryDirectory() as root:
            dest = Path(root) / "lower-growth.xlsm"
            apply_number_cells(source, dest, edits)
            self.assertEqual(float(_cached(dest, PUBLIC, "E20")), -1)
            from lic_dsf_2025_08_12 import Model
            try:
                model = Model.from_workbook(dest)
            except ValueError as exc:
                self.fail(f"negative growth delta was rejected: {exc}")
            actual = model.customized_public_delta.sel(INDICATOR=GROWTH, TIME_PERIOD=2024)
            ok, reason = compare_one(-1, actual)
            self.assertTrue(ok, f"expected -1 at 2024, got {actual!r} ({reason})")


if __name__ == "__main__":
    unittest.main()
