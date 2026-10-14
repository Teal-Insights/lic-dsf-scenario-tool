"""P2 fix batch S11 (split from the spec test file)."""
"""Pre-recording polish S6, S10, S11, S12, S13: copy and placement only, no numbers or limits."""
import unittest

from lic_dsf.hosted import hosted_page

LEAD = ('Using a fictional example country, see how a debt-financed public investment could change its debt outlook '
        'compared with No investment, then download a briefing you can share.')




class FirstActionName(unittest.TestCase):  # S11
    def test_one_name_and_a_primary_button(self):
        page = hosted_page().decode()
        self.assertRegex(page, r'<button id="exampleButton" class="hidden primary"[^>]*>Load the example</button>')
        self.assertIn("'Download and try the official example':'Load the example')", page)
        self.assertIn('<h2>1. Load the example</h2>', page)
        self.assertIn('<span>1 Load the example</span>', page)
        self.assertIn('Start here: click Load the example in step 1.', page)
        for old in ('Try the official illustrative example', 'Start the official illustrative example', 'Start example'):
            self.assertNotIn(old, page)

    def test_tracker_links_only_scroll_to_the_button(self):
        page = hosted_page().decode()
        self.assertIn('<a id="step1" href="#exampleButton"', page)
        self.assertIn('<a id="nextStepLink" href="#exampleButton"', page)
        self.assertIn("const ids=['exampleButton','baseline','scenario','compare','briefing'];", page)
        self.assertIn('>Go to step 1</a>', page)
        self.assertRegex(page, r'#exampleButton\{scroll-margin-top:\d+px\}')
        # Plain fragment links: no script attaches a handler that could load data.
        self.assertNotRegex(page, r"(\$\('|getElementById\(')(step1|nextStepLink)'\)\.(onclick|addEventListener)")
        self.assertEqual(page.count("$('exampleButton').onclick="), 1)


if __name__ == '__main__':
    unittest.main()
