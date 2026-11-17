"""Baked year formulas read the workbook column at the same position."""
import unittest

from lic_dsf.compare import ATOL, compare_one
from lic_dsf.projection_year_shift import (
    install, template_caller, uniform_delta, workbook_caller,
)
from lic_dsf.projection_year_shift import shifted_projection
from lic_dsf_2025_08_12.runtime import CoordinateReader
from lic_dsf_2025_08_12.tensor import Axis, CoordinateError, Domain, Series, TensorSchema


def _series(years, values, series_id):
    time = Axis('TIME_PERIOD', tuple(years), int)
    instrument = Axis('INSTRUMENT', ('IMF',), str)
    domain = Domain.product(instrument, time)
    schema = TensorSchema(series_id, domain, (int, float, type(None)))
    return Series(domain, tuple(values), schema=schema)


class ProjectionYearShift(unittest.TestCase):
    def test_uniform_shift_matches_the_old_debt_snapshot(self):
        from lic_dsf.projection_year_shift import _snapshot
        snapshot = _snapshot()
        shifted = _series((year + 1 for year in snapshot), range(len(snapshot)), 'example')
        self.assertEqual(uniform_delta(shifted), 1)
        self.assertEqual(uniform_delta(_series(snapshot, range(len(snapshot)), 'example')), 0)
        self.assertIsNone(uniform_delta(_series((2024, 2026), (1, 2), 'example')))

    def test_template_read_of_a_workbook_series_keeps_the_column(self):
        from lic_dsf.projection_year_shift import _snapshot
        install()
        snapshot = _snapshot()
        series = _series((year + 1 for year in snapshot), range(len(snapshot)), 'input3_old_debt_service')
        with shifted_projection(1), template_caller():
            ok, reason = compare_one(0, series['IMF', snapshot[0]])
            self.assertTrue(ok, reason)
            ok, reason = compare_one(1, series['IMF', snapshot[1]])
        self.assertTrue(ok, reason)
        self.assertEqual(ATOL, 1e-6)

    def test_workbook_read_of_a_template_series_keeps_the_column(self):
        from lic_dsf.projection_year_shift import _snapshot
        install()
        snapshot = _snapshot()
        series = _series(snapshot, range(len(snapshot)), 'input3_old_debt_service')
        with shifted_projection(1), workbook_caller():
            self.assertEqual(series.sel(INSTRUMENT='IMF', TIME_PERIOD=snapshot[0] + 1), 0)

    def test_same_space_and_inactive_offset_do_not_translate(self):
        from lic_dsf.projection_year_shift import _snapshot
        install()
        snapshot = _snapshot()
        series = _series((year + 1 for year in snapshot), range(len(snapshot)), 'input3_old_debt_service')
        with shifted_projection(1), workbook_caller():
            self.assertEqual(series['IMF', snapshot[0] + 1], 0)
        with self.assertRaises(CoordinateError):
            series['IMF', snapshot[0]]

    def test_reader_iteration_stays_on_its_own_labels(self):
        from lic_dsf.projection_year_shift import _snapshot
        install()
        snapshot = _snapshot()
        workbook = _series((year + 1 for year in snapshot), range(len(snapshot)), 'input3_old_debt_service')
        domain = Domain.product(
            Axis('INSTRUMENT', ('IMF',), str),
            Axis('TIME_PERIOD', tuple(snapshot), int),
        )
        seen = {}

        def formula(instrument, time_period):
            seen['year'] = time_period
            return workbook[instrument, time_period]

        reader = CoordinateReader('input3_old_debt_service', domain, formula)
        with shifted_projection(1):
            self.assertEqual(reader['IMF', snapshot[0]], 0)
        self.assertEqual(seen['year'], snapshot[0])

    def test_baked_year_constants_stay_on_the_series(self):
        from lic_dsf.projection_year_shift import _snapshot
        install()
        snapshot = _snapshot()
        template = _series(snapshot, range(len(snapshot)), 'input3_old_debt_service')
        domain = Domain.product(
            Axis('INSTRUMENT', ('IMF',), str),
            Axis('TIME_PERIOD', tuple(year + 1 for year in snapshot), int),
        )

        def formula(instrument, time_period):
            return template[instrument, snapshot[0]]

        reader = CoordinateReader('input3_old_debt_service', domain, formula)
        with shifted_projection(1):
            self.assertEqual(reader['IMF', snapshot[0] + 1], 0)


if __name__ == '__main__':
    unittest.main()
