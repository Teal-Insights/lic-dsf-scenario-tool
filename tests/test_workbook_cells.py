"""Scenario cell copies replace numbers and leave the original workbook untouched."""
import tempfile
import unittest
import zipfile
from pathlib import Path

from openpyxl import Workbook, load_workbook

from lic_dsf.workbooks import IntakeError, file_hash
from lic_dsf.workbook_cells import apply_number_cells, refresh_cached_numbers


def _store_cached_value(path, old, new):
    """Put a cached result into the sheet XML openpyxl left empty."""
    path = Path(path)
    with zipfile.ZipFile(path) as book:
        members = {info.filename: book.read(info.filename) for info in book.infolist()}
    sheet = "xl/worksheets/sheet1.xml"
    members[sheet] = members[sheet].replace(old.encode(), new.encode(), 1)
    with zipfile.ZipFile(path, "w") as book:
        for name, payload in members.items():
            book.writestr(name, payload)


class WorkbookCells(unittest.TestCase):
    def test_number_cells_replace_formulas_in_a_copy(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            source = root / "source.xlsx"
            book = Workbook()
            sheet = book.active
            sheet.title = "Customized Scenario-External"
            sheet["C21"] = "=1+1"
            sheet["E11"] = 0
            book.save(source)
            book.close()
            original = file_hash(source)
            dest = root / "copy.xlsx"
            apply_number_cells(source, dest, {"Customized Scenario-External": {"C21": 0.125}})
            self.assertEqual(file_hash(source), original)
            edited = load_workbook(dest, data_only=False)
            try:
                cell = edited["Customized Scenario-External"]["C21"]
                self.assertEqual(cell.data_type, "n")
                self.assertEqual(cell.value, 0.125)
                self.assertEqual(edited["Customized Scenario-External"]["E11"].value, 0)
            finally:
                edited.close()

    def test_cached_numbers_keep_the_formula(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            source = root / "source.xlsx"
            book = Workbook()
            sheet = book.active
            sheet.title = "Input 3 - Macro-Debt data(DMX)"
            sheet["X7"] = "=ProjectionYear"
            book.save(source)
            book.close()
            _store_cached_value(source, "<v />", "<v>2024</v>")
            original = file_hash(source)
            dest = root / "copy.xlsx"
            refresh_cached_numbers(source, dest, {"Input 3 - Macro-Debt data(DMX)": {"X7": 2030}})
            self.assertEqual(file_hash(source), original)
            edited = load_workbook(dest, data_only=False)
            try:
                cell = edited["Input 3 - Macro-Debt data(DMX)"]["X7"]
                self.assertEqual(cell.value, "=ProjectionYear")
            finally:
                edited.close()
            cached = load_workbook(dest, data_only=True)
            try:
                self.assertEqual(cached["Input 3 - Macro-Debt data(DMX)"]["X7"].value, 2030)
            finally:
                cached.close()

    def test_missing_cell_is_refused(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            source = root / "source.xlsx"
            book = Workbook()
            book.active.title = "Customized Scenario-External"
            book.active["A1"] = 1
            book.save(source)
            book.close()
            with self.assertRaises(IntakeError) as caught:
                apply_number_cells(source, root / "copy.xlsx", {"Customized Scenario-External": {"C21": 1}})
            self.assertEqual(str(caught.exception), "input_target_missing_from_workbook")


if __name__ == "__main__":
    unittest.main()
