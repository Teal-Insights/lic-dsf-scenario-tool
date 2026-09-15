"""Reviewed teaching inputs are exact, source-bound and independent on every load."""
import hashlib
import unittest
from importlib.resources import files
from unittest.mock import patch

from lic_dsf.illustrative import builtin_investment_cases, OFFICIAL_SHA256, OFFICIAL_YEARS


class BuiltinInvestment(unittest.TestCase):
    def test_admitted_resource_bytes_and_complete_inputs(self):
        expected = {
            'no-investment': '3aa0ad09774bf35eb9e14255d61f11fa041ee60c62c76e1bb7d0388bb343046f',
            'earlier-benefit': '85cff5289a25caa2da2f7a638df739ce458c47ac9f7088ab04515e5d2e0ecb02',
            'smaller-benefit': '873ac66e41fbcdb2ffec6509b3d367270196e91deb0ff285bc9b894c80b8f9d0',
        }
        cases = builtin_investment_cases(OFFICIAL_SHA256, list(OFFICIAL_YEARS))
        self.assertEqual(len(cases), 3)
        for item in cases:
            raw = files('lic_dsf').joinpath('illustrative_cases', item['id'] + '.json').read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), expected[item['id']])
            pack = item['scenario_file']
            self.assertEqual(set(pack), {'format', 'workbook_sha256', 'input_years',
                                         'definition', 'share_label', 'shared_rationale'})
            self.assertEqual(pack['definition']['terms'],
                             {'rate': .08, 'grace_years': 4, 'maturity_years': 9})
            self.assertEqual(sum(map(len, pack['definition']['delta_paths'].values())), 273)
        self.assertEqual(cases[0]['scenario_file']['share_label'], 'No investment')
        self.assertTrue(all(value == 0 for path in cases[0]['scenario_file']['definition']['delta_paths'].values() for value in path))

    def test_other_workbook_or_years_never_get_baseline_specific_inputs(self):
        for sha, years in [
            ('a' * 64, list(OFFICIAL_YEARS)), (OFFICIAL_SHA256.upper(), OFFICIAL_YEARS),
            (OFFICIAL_SHA256, list(range(2025, 2046))),
            (OFFICIAL_SHA256, list(reversed(OFFICIAL_YEARS))),
            (OFFICIAL_SHA256, list(OFFICIAL_YEARS)[:-1]),
            (OFFICIAL_SHA256, [float(x) for x in OFFICIAL_YEARS]),
            (OFFICIAL_SHA256, None),
        ]:
            with self.subTest(sha=sha, years=years):
                self.assertEqual(builtin_investment_cases(sha, years), [])

    def test_returned_draft_mutation_cannot_change_catalog_or_next_load(self):
        first = builtin_investment_cases(OFFICIAL_SHA256, OFFICIAL_YEARS)
        first[1]['scenario_file']['definition']['delta_paths']['20'][6] = 99
        first[1]['scenario_file']['shared_rationale']['20'] = 'Edited privately'
        later = builtin_investment_cases(OFFICIAL_SHA256, OFFICIAL_YEARS)
        self.assertEqual(later[1]['scenario_file']['definition']['delta_paths']['20'][6], .2)
        self.assertNotIn('Edited privately', later[1]['scenario_file']['shared_rationale'].values())

    def test_modified_pack_fails_closed(self):
        with patch('lic_dsf.illustrative.files') as mocked:
            mocked.return_value.joinpath.return_value.read_bytes.return_value = b'{}'
            with self.assertRaisesRegex(ValueError, 'integrity check'):
                builtin_investment_cases(OFFICIAL_SHA256, OFFICIAL_YEARS)


if __name__ == '__main__':
    unittest.main()
