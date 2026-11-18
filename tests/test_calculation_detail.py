"""Calculation failures keep a stable code and can name the worksheet cell."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from lic_dsf.calculation_detail import failure_detail, failure_job, public_detail
from lic_dsf.engine import calculate
from lic_dsf.workbooks import IntakeError


BLEND = ("input4_blend_variant out of domain: 'IDA NEW Blend fixed' "
         "not in {'IDA NEW Blend floating'}")


class CalculationDetailTests(unittest.TestCase):
    def test_blend_variant_names_its_sheet_and_cell(self):
        detail = failure_detail(ValueError(BLEND))
        self.assertEqual(detail, "ValueError at Input 4 - External Financing!D16: " + BLEND)
        self.assertEqual(public_detail(detail), detail)

    def test_coordinate_names_that_cells_row(self):
        from lic_dsf_2025_08_12 import data
        coordinate, address = next(iter(data.INPUT4_BLEND_SCALE_KEY.cells.items()))
        message = (f"input4_blend_scale_key{coordinate!r} out of domain: "
                   "'other' not in {'IDA NEW Regular'}")
        detail = failure_detail(ValueError(message))
        cell = address.split("!")[-1]
        self.assertTrue(cell[0].isalpha() and cell[-1].isdigit(), address)
        self.assertIn(f"Input 4 - External Financing!{cell}", detail)
        self.assertIn(message, detail)

    def test_sequence_index_does_not_invent_a_cell(self):
        message = "input4_interest_rate[0] out of domain: 2 not in {0, 1}"
        detail = failure_detail(ValueError(message))
        self.assertEqual(detail, "ValueError: " + message)
        self.assertNotIn(" at ", detail)

    def test_wrapped_code_reports_the_cause_and_cell(self):
        try:
            raise IntakeError("calculation_failed_private_details_available") from ValueError(BLEND)
        except IntakeError as exc:
            detail = failure_detail(exc)
        self.assertIn("Input 4 - External Financing!D16", detail)
        self.assertNotIn("calculation_failed_private_details_available", detail)

    def test_path_and_traversal_text_are_omitted(self):
        self.assertIsNone(failure_detail(ValueError(r"open C:\Users\analyst\book.xlsm")))
        self.assertIsNone(failure_detail(ValueError(
            "input4_blend_variant out of domain: '../secret' not in {'IDA NEW Blend floating'}")))
        self.assertIsNone(public_detail("ValueError: see /tmp/private.xlsm\nline"))
        self.assertIsNone(public_detail("not a diagnostic"))

    def test_a_slash_omits_the_diagnostic(self):
        message = ("input4_blend_variant out of domain: 'A/B' "
                   "not in {'IDA NEW Blend floating'}")
        self.assertIsNone(failure_detail(ValueError(message)))

    def test_job_keeps_the_stable_sentence_and_a_separate_detail(self):
        cause = ValueError(BLEND)
        failed = IntakeError("calculation_failed_private_details_available")
        failed.detail = failure_detail(cause)
        job = failure_job(failed, "scenario")
        self.assertEqual(job["message"], "calculation_failed_private_details_available")
        self.assertIn("Input 4 - External Financing!D16", job["detail"])
        self.assertNotIn("detail", failure_job(ValueError("see /tmp/private.xlsm"), "scenario"))

    def test_calculate_attaches_the_cell_without_replacing_the_code(self):
        with patch("lic_dsf.engine._calculate", side_effect=ValueError(BLEND)):
            with self.assertRaises(IntakeError) as caught:
                calculate("unused.xlsm")
        self.assertEqual(str(caught.exception), "calculation_failed_private_details_available")
        self.assertIn("Input 4 - External Financing!D16", caught.exception.detail)

    def test_worker_records_the_cell_in_error_json(self):
        source = Path(__file__).resolve().parents[1] / "src"
        with tempfile.TemporaryDirectory(prefix="lic-dsf-detail-") as folder:
            request = Path(folder) / "request.json"
            request.write_text(json.dumps({
                "workbook": "unused.xlsm", "workbook_sha256": "a" * 64,
                "scenario": None, "parent_pid": os.getpid(), "deadline_utc": time.time() + 30,
            }), encoding="utf-8")
            code = r'''
import sys
import threading
import lic_dsf
from lic_dsf import worker
from lic_dsf.workbooks import IntakeError
def calculate(workbook, scenario, expected_sha256=None):
    raise IntakeError("calculation_failed_private_details_available") from ValueError(
        "input4_blend_variant out of domain: 'IDA NEW Blend fixed' "
        "not in {'IDA NEW Blend floating'}")
lic_dsf.calculate = calculate
worker.start_guard = lambda request, directory: threading.Event()
raise SystemExit(worker.main(sys.argv[1]))
'''
            env = dict(os.environ, PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE="1")
            run = subprocess.run([sys.executable, "-c", code, str(request)],
                                 env=env, capture_output=True, timeout=60)
            error = json.loads((Path(folder) / "error.json").read_text(encoding="utf-8"))
        self.assertEqual(run.returncode, 1, run.stderr.decode("utf-8", errors="replace"))
        self.assertEqual(error["code"], "calculation_failed_private_details_available")
        self.assertIn("Input 4 - External Financing!D16", error["detail"])

    def test_page_shows_the_detail_beside_calculate(self):
        page = (Path(__file__).resolve().parents[1] / "src" / "lic_dsf" / "web.html").read_text(encoding="utf-8")
        self.assertIn('id="calcDetail"', page)
        self.assertIn("showCalcDetail(job.detail)", page)
        self.assertIn("el.textContent=shown", page)


if __name__ == "__main__":
    unittest.main()
