"""P2 fix batch S6 (split from the spec test file)."""
"""Pre-recording polish S6, S10, S11, S12, S13: copy and placement only, no numbers or limits."""
import unittest

from lic_dsf.hosted import landing

LEAD = ('Using a fictional example country, see how a debt-financed public investment could change its debt outlook '
        'compared with No investment, then download a briefing you can share.')




class LandingLead(unittest.TestCase):  # S6
    def test_lead_sits_under_the_heading_and_the_guided_route_before_the_start_button(self):
        page = landing().decode()
        self.assertIn('<p class="lead">' + LEAD + '</p>', page)
        self.assertLess(page.index('</h1>'), page.index(LEAD))
        self.assertLess(page.index(LEAD), page.index('What this site is'))
        guided = '<strong>Guided example:</strong> compare two investment teaching cases with No investment.'
        self.assertIn(guided, page)
        self.assertLess(page.index(guided), page.index('id="begin"'))
        for kept in ('Illustrative', '>Start an illustrative visit</button>', '12 simultaneous visits', '30 completed exports',
                     'releases/tag/v0.1.0-alpha.2'):
            self.assertIn(kept, page)
        self.assertNotIn('of GDP', LEAD)


if __name__ == '__main__':
    unittest.main()
