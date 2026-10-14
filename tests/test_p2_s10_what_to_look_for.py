"""P2 fix batch S10 (split from the spec test file)."""
"""Pre-recording polish S6, S10, S11, S12, S13: copy and placement only, no numbers or limits."""
import json
import re
import unittest
from importlib.resources import files

from lic_dsf.illustrative import (
    OFFICIAL_SHA256,
    OFFICIAL_YEARS,
    builtin_investment_cases,
)

LEAD = ('Using a fictional example country, see how a debt-financed public investment could change its debt outlook '
        'compared with No investment, then download a briefing you can share.')




class WhatToLookFor(unittest.TestCase):  # S10: every claim in the lines is checked against the teaching inputs
    def test_lines_are_true_for_the_prepared_cases(self):
        cases = {c['id']: c['scenario_file'] for c in builtin_investment_cases(OFFICIAL_SHA256, list(OFFICIAL_YEARS))}
        web = (files('lic_dsf') / 'web.html').read_text()
        table = re.search(r'const BUILTIN_LOOK_FOR=(\{.*?\});\n', web).group(1)
        lines = json.loads(table.replace("'", '"'))
        self.assertEqual(set(lines), set(cases))
        # Same borrowing terms in all three cases; No investment adds nothing.
        self.assertEqual(len({json.dumps(c['definition']['terms'], sort_keys=True) for c in cases.values()}), 1)
        self.assertTrue(all(v == 0 for path in cases['no-investment']['definition']['delta_paths'].values() for v in path))
        larger, smaller = cases['earlier-benefit'], cases['smaller-benefit']
        # Same upfront investment and maintenance: identical spending rationale, upfront years and import content.
        self.assertEqual(larger['shared_rationale']['13'], smaller['shared_rationale']['13'])
        self.assertEqual(larger['definition']['delta_paths']['13'][:6], smaller['definition']['delta_paths']['13'][:6])
        self.assertEqual(larger['definition']['delta_paths']['30'], smaller['definition']['delta_paths']['30'])
        self.assertGreater(max(larger['definition']['delta_paths']['20']), max(smaller['definition']['delta_paths']['20']))
        self.assertIn('larger assumed growth benefit', lines['earlier-benefit'])
        self.assertIn('smaller assumed growth benefit', lines['smaller-benefit'])
        for text in lines.values():  # no outcome claims, no units
            self.assertNotRegex(text.lower(), r'lower|higher|better|worse|reduc|improv|sustainab|of gdp|pp\b')
        # Spending as entered (a share of GDP) differs after 2029, so the lines must not say "same spending".
        self.assertNotEqual(larger['definition']['delta_paths']['13'], smaller['definition']['delta_paths']['13'])
        self.assertNotIn('same spending', ' '.join(lines.values()).lower())


if __name__ == '__main__':
    unittest.main()


if __name__ == '__main__':
    unittest.main()
