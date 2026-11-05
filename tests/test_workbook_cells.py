"""Scenario cell copies replace numbers and leave the original workbook untouched."""
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook, load_workbook

from lic_dsf.workbooks import IntakeError, file_hash
from lic_dsf.workbook_cells import apply_number_cells


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
