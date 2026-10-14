"""P2 fix batch S12 (split from the spec test file)."""
"""Pre-recording polish S6, S10, S11, S12, S13: copy and placement only, no numbers or limits."""
import unittest

from lic_dsf.hosted import hosted_page

LEAD = ('Using a fictional example country, see how a debt-financed public investment could change its debt outlook '
        'compared with No investment, then download a briefing you can share.')




class StepThreeOrder(unittest.TestCase):  # S12
    def test_teaching_box_first_then_build_your_own(self):
        page = hosted_page().decode()
        step3 = page[page.index('<section id="scenario"'):page.index('<section id="compare"')]
        order = ['<div id="editor"', '<section id="builtinInvestment"', '<h3 id="buildOwnTitle">Build your own scenario</h3>',
                 'id="newZero"', 'id="newImported"', 'id="duplicate"', 'id="discard"', 'id="dirty"',
                 '<details id="scenarioExchange">', '<details id="presetOptions"', 'class="toolbar save-bar"']
        positions = [step3.index(marker) for marker in order]
        self.assertEqual(positions, sorted(positions))
        group = step3[step3.index('id="buildOwnTitle"'):step3.index('<details id="scenarioExchange">')]
        self.assertIn('role="group" aria-labelledby="buildOwnTitle"', group)
        self.assertNotIn('<details', group)  # status messages point to Discard unsaved edits: it stays visible
        for button in ('newZero', 'newImported', 'duplicate', 'discard'):
            self.assertEqual(page.count(f'id="{button}"'), 1)

    def test_messages_point_to_where_discard_now_sits(self):
        page = hosted_page().decode()
        self.assertNotIn('(top of step 3)', page)
        self.assertIn('Discard unsaved edits (under Build your own scenario in step 3)', page)


if __name__ == '__main__':
    unittest.main()
