"""Step 5 results order (S2) and the next-step bar markup (S3), desktop and hosted."""
import unittest
from pathlib import Path

from lic_dsf.hosted import hosted_page

WEB = Path(__file__).parents[1] / 'src/lic_dsf/web.html'
ORDER = ('id="teachingNext"', 'id="takeaways"', '<h3>Policy briefing charts</h3>',
         '<h3>Standard LIC-DSF charts</h3>', 'id="packet"', 'id="labelPanel"')


def briefing(page):
    start = page.index('<section id="briefing"')
    return page[start:page.index('</section>', start)]


class ResultsOrder(unittest.TestCase):
    def check(self, page):
        section = briefing(page)
        positions = [section.index(marker) for marker in ORDER]
        self.assertEqual(positions, sorted(positions))
        self.assertLess(section.index('id="teachingNext"'), section.index('id="chartsStatus"'))
        self.assertIn('<div id="teachingNext" class="notice teaching-next hidden" role="region" aria-label="Next step">', section)
        self.assertIn('<details class="label-panel" id="labelPanel"><summary>Edit chart heading and legend labels (optional)</summary>', section)
        self.assertIn('>Download the briefing packet (.zip)</button>', section)
        packet = section[section.index('<div class="export-packet">'):section.index('<details id="moreDownloads"')]
        self.assertNotIn('complete', packet.lower())
        for id_ in ('chartContextLabel', 'legendLabels', 'saveChartContext', 'discardChartContext', 'chartContextState', 'packet', 'preparedPacketRecovery', 'chart', 'chartBriefing'):
            self.assertEqual(section.count(f'id="{id_}"'), 1, id_)

    def test_desktop_order(self):
        self.check(WEB.read_text(encoding='utf-8'))

    def test_hosted_order_and_no_complete_packet(self):
        page = hosted_page().decode()
        self.check(page)
        self.assertNotIn('complete briefing packet', page)
        self.assertIn('final slot is reserved for Download the briefing packet', page)

class DownloadIsFoundAfterTheCharts(unittest.TestCase):
    """Both fresh first-time-user sessions hunted for the download: every pointer now says it sits below the charts."""
    def test_pointers_say_where_the_download_is(self):
        html = (Path(__file__).resolve().parents[1] / 'src' / 'lic_dsf' / 'web.html').read_text(encoding='utf-8')
        self.assertIn("Both chart views are ready. Review them, then download the briefing packet below the charts.", html)
        self.assertIn('review the charts, then download the packet below them.', html)
        self.assertIn("'Review both charts, then download the briefing packet below them.", html)


if __name__ == '__main__':
    unittest.main()
