"""Pin the numbers each chart is drawn from: series, thresholds, zero lines and end-point anchors.

Only data arguments are recorded, never style keywords, headings or footers, so a style-sheet or
stamp change cannot trip this test while a moved threshold, flipped sign or relabelled series does.
"""
import hashlib
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib  # noqa: E402

matplotlib.use('Agg')
from matplotlib.axes import Axes  # noqa: E402

from lic_dsf import charts  # noqa: E402
from test_charts import fixture  # noqa: E402

GOLDEN = 'ebb0e4c8c094ecca02072b3882a298a367005f56ac87428249556f6557cea7ba'


def _num(values):
    try:
        return [None if x != x else round(float(x), 12) for x in values]
    except TypeError:
        return None if values != values else round(float(values), 12)


def digest():
    calls = []
    real = {name: getattr(Axes, name) for name in ('plot', 'axhline', 'annotate')}

    def plot(self, *args, **kwargs):
        calls.append(['plot', kwargs.get('label'), [_num(a) for a in args if not isinstance(a, str)]])
        return real['plot'](self, *args, **kwargs)

    def axhline(self, y=0, *args, **kwargs):
        calls.append(['hline', _num(y)])
        return real['axhline'](self, y, *args, **kwargs)

    def annotate(self, text, xy, *args, **kwargs):
        calls.append(['anchor', _num(xy[0]), _num(xy[1])])
        return real['annotate'](self, text, xy, *args, **kwargs)

    with patch.multiple(Axes, plot=plot, axhline=axhline, annotate=annotate):
        for view in ('standard', 'briefing'):
            for metric, *_ in charts.METRICS:
                calls.append(['indicator', view, metric])
                charts.render_indicator(fixture(), metric, view, 'png')
    return hashlib.sha256(json.dumps(calls, sort_keys=True).encode()).hexdigest()


class ChartDataInvariance(unittest.TestCase):
    def test_plotted_data_unchanged(self):
        self.assertEqual(digest(), GOLDEN)


if __name__ == '__main__':
    print(digest())
