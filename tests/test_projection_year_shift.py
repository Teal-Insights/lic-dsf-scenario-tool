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

    def test_issuance_year_used_as_time_follows_the_projection_year(self):
        install()
        stock, baked = _vintage_stock()
        domain = stock.domain

        def formula(instrument, holder, issuance_year, time_period):
            return stock[instrument, holder, issuance_year, issuance_year]

        reader = CoordinateReader('input5_vintage_principal', domain, formula)
        with shifted_projection(1):
            first = reader['Central bank financing', 'residents', baked[0], baked[0] + 1]
            later = reader['Central bank financing', 'residents', baked[1], baked[4] + 1]
        self.assertEqual(first, 0)
        self.assertEqual(later, 1)

    def test_neighboring_year_stays_when_it_matches_the_issuance_label(self):
        install()
        stock, baked = _vintage_stock()

        def formula(instrument, holder, issuance_year, time_period):
            return stock[instrument, holder, baked[5], baked[5]]

        reader = CoordinateReader('input5_vintage_principal', stock.domain, formula)
        with shifted_projection(1):
            found = reader['Central bank financing', 'residents', baked[5], baked[5] + 1]
        self.assertEqual(found, 4)

    def test_vintage_label_on_a_time_series_follows_the_projection_year(self):
        from lic_dsf.projection_year_shift import _baked_keys
        install()
        baked = _baked_keys('input5_projection_years')
        time = Axis('TIME_PERIOD', tuple(year + 1 for year in baked), int)
        domain = Domain.product(time)
        schema = TensorSchema('input5_projection_years', domain, (int, float, type(None)))
        years = Series(domain, tuple(range(len(baked))), schema=schema)
        vintage = Domain.product(Axis('ISSUANCE_YEAR', (baked[1],), int))

        def anchored(issuance_year):
            return years[issuance_year]

        reader = CoordinateReader('input5_vintage_issuance_year', vintage, anchored)
        with shifted_projection(1):
            self.assertEqual(reader[baked[1]], baked.index(baked[1]))

    def test_other_year_on_a_time_series_stays_written(self):
        install()
        stock, baked = _vintage_stock()
        time = stock.domain.axis('TIME_PERIOD')
        domain = Domain.product(time)
        schema = TensorSchema('input5_vintage_stock', domain, (int, float, type(None)))
        years = Series(domain, tuple(range(len(baked))), schema=schema)

        def formula(instrument, holder, issuance_year, time_period):
            return years[baked[2]]

        reader = CoordinateReader('input5_vintage_principal', stock.domain, formula)
        with shifted_projection(1):
            found = reader['Central bank financing', 'residents', baked[0], baked[4] + 1]
        self.assertEqual(found, 1)


def _vintage_stock():
    from lic_dsf.projection_year_shift import _baked_keys
    baked = _baked_keys('input5_vintage_stock')
    instrument = Axis('INSTRUMENT', ('Central bank financing',), str)
    holder = Axis('HOLDER', ('residents',), str)
    issuance = Axis('ISSUANCE_YEAR', baked, int)
    time = Axis('TIME_PERIOD', tuple(year + 1 for year in baked), int)
    domain = Domain.product(instrument, holder, issuance, time)
    values = tuple(
        time_index
        for _instrument in instrument.keys
        for _holder in holder.keys
        for _issuance in issuance.keys
        for time_index, _year in enumerate(time.keys)
    )
    schema = TensorSchema('input5_vintage_stock', domain, (int, float, type(None)))
    return Series(domain, values, schema=schema), baked


if __name__ == '__main__':
    unittest.main()
