"""A shifted projection year must match Excel on every sampled probe.

The workbook is the Excel-recalculated public converter output. It is
gitignored and is not committed. The check fails closed when that file is
absent. It fails when any of the 76 probes disagrees at the locked tolerance.
"""
import os
from pathlib import Path
import unittest

from lic_dsf.compare import ATOL
from lic_dsf.engine import calculate
from lic_dsf.ida21 import probes

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / '2026-11-16_public-repro_converter-output_calc-fails.xlsm'


def _workbook():
    override = os.environ.get('DSF_SHIFTED_WORKBOOK')
    return Path(override) if override else DEFAULT


class ShiftedProjectionProbes(unittest.TestCase):
    maxDiff = None

    def test_every_probe_matches_excel(self):
        self.assertEqual(ATOL, 1e-6)
        self.assertEqual(len(probes()), 76)
        path = _workbook()
        self.assertTrue(path.is_file(), f'Excel-recalculated workbook is required: {path}')
        evidence = calculate(path)['evidence']
        self.assertEqual(evidence['cache_total'], 76)
        mismatches = evidence['cache_mismatch_probes']
        self.assertEqual(
            mismatches,
            [],
            f"{evidence['cache_passed']} of {evidence['cache_total']} probes matched Excel at {ATOL}",
        )
        self.assertEqual(evidence['cache_passed'], 76)
        self.assertEqual(evidence['saved_cache'], 'matched')


if __name__ == '__main__':
    unittest.main()
