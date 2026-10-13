"""The hosted demo never names the country whose labels the template's sample data carry.

The banned words are stored only as SHA-256 hashes (name, demonym, ISO code, capital, currency),
so this file does not spell them either. Every word on each user-facing surface is hashed and checked.
"""
import hashlib
import io
import json
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

BANNED = {
    'fc4f9c94394e55c0c42baa313bb1d8717a4024c671ead9b4faae1eb81ff2edba',
    'e04701a0e18513432ef7f0b68d7aa65148300fec6bd72367f95cd504eed4782c',
    '7b40163cdd960bd35d184edf8473137a84aa3600771fd627db7182c647f22adc',
    'fb0b23773a1f394e1a57e9e2fdbc97015aad731444bb1dc32ea056a76e918be7',
    'c108f9afa4843d204942ed0ddd9146de4c229979991b150a1089d4be71b0298e',
    '20b5a4e2e38652535efd949fcefcb148c25014ec201113f5ba5290021d47a2df',
    '333404af0ba310662394241fe9ba5a591a406a05b0acd4f8d3a4e822ad5fcb95',
}


def named(text):
    """Return the banned words found in text, as hashes."""
    return sorted({h for h in (hashlib.sha256(w.lower().encode()).hexdigest() for w in re.findall(r'[A-Za-z]+', text)) if h in BANNED})


def official(comparison):
    from lic_dsf.charts import OFFICIAL_EXAMPLE_SHA
    comparison['workbook_sha256'] = OFFICIAL_EXAMPLE_SHA
    if comparison.get('chart_context'):
        comparison['chart_context']['workbook_sha256'] = OFFICIAL_EXAMPLE_SHA
    for run in comparison['runs']:
        run['result']['workbook_sha256'] = OFFICIAL_EXAMPLE_SHA
    return comparison


class NoCountryName(unittest.TestCase):
    def test_served_pages_and_disclosures(self):
        from lic_dsf import charts
        from lic_dsf.hosted import DISCLOSURE, hosted_page, landing
        root = Path(__file__).resolve().parents[1] / 'src' / 'lic_dsf'
        surfaces = {'landing': landing().decode(), 'hosted page': hosted_page().decode(), 'hosted disclosure': DISCLOSURE,
                    'chart disclosure': charts.ILLUSTRATIVE_DISCLOSURE, 'web.html': (root / 'web.html').read_text(),
                    'hosted_wait.js': (root / 'hosted_wait.js').read_text()}
        for name, text in surfaces.items():
            self.assertEqual(named(text), [], name)
        self.assertIn('Macronia', charts.ILLUSTRATIVE_DISCLOSURE)

    def test_official_example_exports(self):
        from matplotlib.axes import Axes
        from matplotlib.figure import Figure
        from lic_dsf import charts
        from lic_dsf.app import shareable
        from lic_dsf.briefing_pack import render_pack, tables, workbook_bytes
        from test_briefing_pack import public_fixture
        c = official(public_fixture())
        shared = shareable(official(json.loads(json.dumps(c))))
        self.assertEqual(named(json.dumps(shared)), [], 'shared comparison JSON')
        self.assertIn('Macronia', shared['workbook_provenance']['disclosure'])
        with patch('lic_dsf.briefing_pack.render_comparison', return_value=b'PDF'), patch('lic_dsf.briefing_pack.render_indicator', return_value=b'CHART'):
            blob = render_pack(c)
        with ZipFile(io.BytesIO(blob)) as z:
            for name in z.namelist():
                if name.endswith(('.txt', '.json', '.csv')):
                    self.assertEqual(named(z.read(name).decode('utf-8-sig')), [], name)
        with ZipFile(io.BytesIO(workbook_bytes(tables(c), c))) as x:
            for name in x.namelist():
                if name.endswith('.xml'):
                    self.assertEqual(named(x.read(name).decode('utf-8')), [], 'tables.xlsx ' + name)
        drawn = []
        real = {'fig': Figure.text, 'ax': Axes.text}
        def fig_text(self, x, y, s, *a, **k):
            drawn.append(str(s)); return real['fig'](self, x, y, s, *a, **k)
        def ax_text(self, x, y, s, *a, **k):
            drawn.append(str(s)); return real['ax'](self, x, y, s, *a, **k)
        with patch.object(Figure, 'text', fig_text), patch.object(Axes, 'text', ax_text):
            for view in ('standard', 'briefing'):
                charts.render_indicator(c, 'ext_pv_gdp', view, 'png')
                charts.render_comparison(c, view, 'png')
        self.assertTrue(drawn)
        self.assertEqual(named('\n'.join(drawn)), [], 'text drawn on charts')


if __name__ == '__main__':
    unittest.main()
