"""Official template with the projection axis moved from 2024 to 2025.

The generated library bakes the template calendar into its formulas. This
case checks that calculated chart samples still match the official workbook
at the same projection offset. The tolerance stays 1e-6. The official
workbook is downloaded for the test and is not committed.
"""
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
import urllib.request

from openpyxl import load_workbook

from lic_dsf.compare import ATOL, compare_one
from lic_dsf.engine import calculate
from lic_dsf.ida21 import METRICS, cell
from lic_dsf.workbook_cells import apply_number_cells, refresh_cached_numbers
from lic_dsf.workbooks import IntakeError, inspect_workbook

OFFICIAL_URL = (
    "https://thedocs.worldbank.org/en/doc/"
    "f0ade6bcf85b6f98dbeb2c39a2b7770c-0360012025/original/"
    "LIC-DSF-IDA21-Template-08-12-2025-vf.xlsm"
)
OFFICIAL_SHA256 = "3a0a0b80c7cbc95ac953f25ecae0b437129d669ceb8aeefb54ab86dc8727ea86"
FIRST_YEAR = 2025
TEMPLATE_YEAR = 2024
# Baseline PV of PPG external debt-to-GDP at the template's first projection year.
BASELINE_PV_GDP = 44.88462374681342


def _official():
    override = os.environ.get("DSF_OFFICIAL_WORKBOOK")
    if override:
        path = Path(override)
    else:
        path = Path(tempfile.gettempdir()) / f"lic-dsf-official-{OFFICIAL_SHA256[:12]}.xlsm"
        if not path.is_file():
            urllib.request.urlretrieve(OFFICIAL_URL, path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != OFFICIAL_SHA256:
        raise AssertionError(f"official workbook sha256 {digest} != {OFFICIAL_SHA256}")
    return path


def _sheet_address(address):
    if address.startswith("'"):
        sheet, coord = address[1:].split("'!")
        return sheet.replace("''", "'"), coord
    sheet, coord = address.split("!")
    return sheet, coord


def _year_header_edits(source, shift):
    """Move every cached year header the loader and intake read, by one shift."""
    from lic_dsf_2025_08_12 import data

    book = load_workbook(source, read_only=True, data_only=True, keep_links=False)
    edits = {}
    try:
        seen = set()
        addresses = []
        for axes in data.LABEL_CELLS.values():
            addresses.extend(axes.get("TIME_PERIOD", ()))
        for _metric, _title, _units, sheet, _base, _custom, col, header in METRICS:
            for offset in range(21):
                addresses.append(f"'{sheet}'!{cell(col + offset, header)}")
        for address in addresses:
            if address in seen:
                continue
            seen.add(address)
            sheet, coord = _sheet_address(address)
            edits.setdefault(sheet, {})[coord] = int(book[sheet][coord].value) + shift
    finally:
        book.close()
    return edits


def _points(result):
    origin = result["first_projection_year"]
    return {(point["metric"], point["year"] - origin): point for point in result["points"]}


class ShiftedProjection(unittest.TestCase):
    maxDiff = None

    def test_projection_year_2025_matches_official_offset(self):
        """A one-year-later axis matches the official workbook at the same offset."""
        self.assertEqual(ATOL, 1e-6)
        source = _official()
        try:
            official = calculate(source)
        except IntakeError as exc:
            raise AssertionError(exc.__cause__ or exc) from exc
        self.assertEqual(official["first_projection_year"], TEMPLATE_YEAR)
        self.assertEqual(official["evidence"]["saved_cache"], "matched")
        self.assertEqual(official["evidence"]["cache_passed"], official["evidence"]["cache_total"])
        self.assertEqual(official["evidence"]["calculation"], "computed_unverified")
        official_points = _points(official)
        baseline = official_points[("ext_pv_gdp", 0)]["reference_baseline"]
        ok, reason = compare_one(BASELINE_PV_GDP, baseline)
        self.assertTrue(ok, f"official PV/GDP at 2024 was {baseline!r} ({reason})")

        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            dated = root / "dated.xlsm"
            shifted_path = root / "shifted.xlsm"
            refresh_cached_numbers(source, dated, _year_header_edits(source, FIRST_YEAR - TEMPLATE_YEAR))
            apply_number_cells(
                dated,
                shifted_path,
                {"Input 1 - Basics": {"C17": FIRST_YEAR, "C18": FIRST_YEAR}},
            )
            info = inspect_workbook(shifted_path)
            self.assertEqual(info["compatibility"]["errors"], [])
            self.assertEqual(info["compatibility"]["status"], "supported")
            self.assertEqual(info["first_projection_year"], FIRST_YEAR)
            self.assertEqual(info["input_years"][0], FIRST_YEAR)
            try:
                shifted = calculate(shifted_path)
            except IntakeError as exc:
                raise AssertionError(exc.__cause__ or exc) from exc
        self.assertEqual(shifted["first_projection_year"], FIRST_YEAR)
        self.assertEqual(shifted["evidence"]["saved_cache"], "matched")
        self.assertEqual(shifted["evidence"]["cache_passed"], shifted["evidence"]["cache_total"])
        self.assertEqual(shifted["evidence"]["cache_mismatch_probes"], [])
        self.assertEqual(shifted["evidence"]["calculation"], "computed_unverified")
        shifted_points = _points(shifted)
        self.assertEqual(set(official_points), set(shifted_points))
        worst = 0.0
        for key, original in official_points.items():
            moved = shifted_points[key]
            self.assertEqual(moved["year"], FIRST_YEAR + key[1])
            for field in ("reference_baseline", "as_supplied_customized", "scenario"):
                ok, reason = compare_one(original[field], moved[field])
                self.assertTrue(
                    ok,
                    f"{key} {field}: official {original[field]!r}, "
                    f"shifted {moved[field]!r} ({reason})",
                )
                if isinstance(original[field], (int, float)) and not isinstance(original[field], bool):
                    worst = max(worst, abs(float(original[field]) - float(moved[field])))
        self.assertLessEqual(worst, ATOL)
        moved_baseline = shifted_points[("ext_pv_gdp", 0)]["reference_baseline"]
        ok, reason = compare_one(BASELINE_PV_GDP, moved_baseline)
        self.assertTrue(ok, f"shifted PV/GDP at 2025 was {moved_baseline!r} ({reason})")


if __name__ == "__main__":
    unittest.main()
