"""P2 fix batch S13 (split from the spec test file)."""
"""Pre-recording polish S6, S10, S11, S12, S13: copy and placement only, no numbers or limits."""
import unittest

from lic_dsf.hosted import hosted_page

LEAD = ('Using a fictional example country, see how a debt-financed public investment could change its debt outlook '
        'compared with No investment, then download a briefing you can share.')




class DeleteAtBottom(unittest.TestCase):  # S13
    def test_delete_is_a_quiet_footer_button_with_the_same_wiring(self):
        page = hosted_page().decode()
        aside = page[page.index('<aside class="card">'):page.index('</aside>')]
        self.assertNotIn('deleteVisit', aside)
        footer = page[page.index('<footer>'):page.index('</footer>')]
        self.assertIn('<button id="deleteVisit" type="button"', footer)
        self.assertIn('>Delete my work and return to the start</button>', footer)
        self.assertEqual(page.count('id="deleteVisit"'), 1)
        self.assertLess(page.index('id="deleteVisit"'), page.index("document.getElementById('deleteVisit').onclick=deleteHostedVisit;"))
        self.assertRegex(page, r'#deleteVisit\{background:none;border:0;padding:0;[^}]*text-decoration:underline')
        self.assertIn('#deleteVisit[data-hint]::after{top:auto;bottom:calc(100% + 6px)}', page)


if __name__ == '__main__':
    unittest.main()
