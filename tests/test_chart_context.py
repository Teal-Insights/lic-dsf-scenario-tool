import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "chart_context_test", Path(__file__).parents[1] / "src/lic_dsf/chart_context.py"
)
context = importlib.util.module_from_spec(spec)
spec.loader.exec_module(context)


class ChartContextTests(unittest.TestCase):
    def test_deliberate_text_and_fiscal_years(self):
        for label in ("Budget: FY2030/31", "FY2030/2031", "2030/31", "2030/2031",
                      "FY30/31", "FY 2030/31", "fy 99/00", "FY1999/00",
                      "Résumé — budget (2030)", "$20 {draft}_<example>", "A" * 80):
            with self.subTest(label=label):
                self.assertEqual(context.normalize_context_label(label), label)
        self.assertEqual(context.normalize_context_label("  Re\u0301sume\u0301  "), "Résumé")
        self.assertIsNone(context.normalize_context_label("   "))
        self.assertIsNone(context.normalize_context_label(None))

    def test_paths_links_controls_and_false_fiscal_years(self):
        for label in ("/tmp/example", "~/draft", "../draft", "folder/file", r"C:\example", "C:private", "Ｃ：private",
                      "file:///example", "https://example.test", "www.example.test", "report.xlsx",
                      "Append report.PDF here", "folder／file", "C:＼example", "Budget/outturn",
                      "FY2030/32", "FY2030/2029", "30/31", "FY30/2031", "a2030/31b",
                      "FY2030/31/file", "FY2030/31\n", "hidden\u200b", "hidden\u202e",
                      "a\u2028b", "a\x00b", "A" * 81, 3, True, {}, []):
            with self.subTest(label=repr(label)):
                with self.assertRaises(ValueError) as caught:
                    context.normalize_context_label(label)
                if isinstance(label, str) and len(label) > 10:
                    self.assertNotIn(label, str(caught.exception))

    def test_record_is_exact_canonical_and_source_bound(self):
        sha = "a" * 64
        base = {"workbook_sha256": sha, "label": None, "revision": 0}
        self.assertEqual(context.validate_chart_context(base, sha), base)
        labelled = dict(base, label="Illustrative analysis", revision=1)
        self.assertEqual(context.validate_chart_context(labelled, sha), labelled)
        for record in (dict(base, extra="private"), dict(base, workbook_sha256="b" * 64),
                       dict(base, label="Label"), dict(base, revision=True),
                       dict(base, revision=-1), dict(base, revision=1.5),
                       dict(labelled, label=" Label "), dict(labelled, label="Re\u0301sume\u0301"),
                       {"label": None, "revision": 0}, None):
            with self.subTest(record=record), self.assertRaises(ValueError):
                context.validate_chart_context(record, sha)
        for invalid_sha in ("A" * 64, "a" * 12, None, 3):
            with self.assertRaises(ValueError):
                context.validate_chart_context(base, invalid_sha)


if __name__ == "__main__":
    unittest.main()
