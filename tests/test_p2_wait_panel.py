"""S7: hosted wait panel copy and button placement (add to tests/test_hosted_recovery.py)."""
import re
import unittest
from pathlib import Path

from lic_dsf.hosted import hosted_page


class WaitPanelCopy(unittest.TestCase):
    def setUp(self):
        self.page = hosted_page().decode()

    def test_panel_button_says_cancel_and_moves_off_calculate(self):
        panel = self.page[self.page.index('<div id="exportWaitPanel"'):self.page.index('</aside>')]
        self.assertRegex(panel, r'<button id="cancelQueuedExport" type="button" data-hint="[^"]+">Cancel</button>')
        self.assertNotIn('export', re.sub(r'id="[^"]*"', '', panel).lower())
        self.assertRegex(self.page, r'#exportWaitPanel\{[^}]*display:flex[^}]*\}')
        self.assertIn('#cancelQueuedExport{margin-left:auto}', self.page)
        self.assertIn('#cancelQueuedExport[data-hint]::after{top:auto;bottom:calc(100% + 6px);left:auto;right:0}', self.page)

    def test_calculate_and_chart_drawing_are_named(self):
        self.assertIn("status('Calculating and drawing the charts…')", self.page)
        self.assertIn("format:'svg',metric:$('chartMetric').value},true,'charts');blobs.push(", self.page)

    def test_wait_script_never_says_export(self):
        js = (Path(__import__('lic_dsf').__file__).parent / 'hosted_wait.js').read_text(encoding='utf-8')
        shown = re.findall(r"exportWaitText\('([^']*)'\)", js) + re.findall(r"throw Error\('([^']*)'\)", js)
        self.assertTrue(shown)
        for text in ('Drawing the charts…', 'Preparing your briefing packet…', "'Queued: position '"):
            self.assertIn(text, js)
        for text in re.findall(r"exportWaitText\('([^']*)'\)", js):
            self.assertNotIn('export', text.lower(), text)
        # Messages thrown while charts are drawn or a download is prepared do not call it an export either.
        for text in re.findall(r"throw Error\((?:[\w.]+\|\|)?'([^']*)'\)", js):
            self.assertNotIn('export', text.lower(), text)

    def test_landing_makes_no_unmeasured_time_promise(self):
        from lic_dsf.hosted import landing
        self.assertNotIn('one to two minutes', landing().decode())


if __name__ == '__main__':
    unittest.main()
