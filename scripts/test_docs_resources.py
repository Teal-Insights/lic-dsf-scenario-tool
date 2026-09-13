"""Regression checks for resources missed by the earlier HTML-only check."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CHECKER = Path(__file__).with_name('check_docs.py')


class ResourceChecks(unittest.TestCase):
    def check_site(self, html, css=''):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / 'index.html').write_text(html, encoding='utf-8')
            (root / 'theme.css').write_text(css, encoding='utf-8')
            return subprocess.run([sys.executable, str(CHECKER), '--site', name],
                                  capture_output=True, text=True)

    def test_remote_import_in_local_stylesheet_is_rejected(self):
        result = self.check_site('<link rel="stylesheet" href="theme.css">',
                                 '@import url("https://example.com/font.css");')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('remote page resource', result.stdout)

    def test_css_escape_cannot_hide_remote_font(self):
        result = self.check_site('<p>Example</p>',
                                 r'@font-face{src:url(\68 ttps://example.com/font.woff2)}')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('remote page resource', result.stdout)

    def test_missing_local_font_is_rejected(self):
        result = self.check_site('<p>Example</p>', '@font-face{src:url(missing.otf)}')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('missing or outside site', result.stdout)

    def test_remote_srcset_is_rejected(self):
        result = self.check_site('<img srcset="https://example.com/image.png 2x">')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('remote page resource', result.stdout)

    def test_inline_remote_style_is_rejected(self):
        result = self.check_site('<p style="background:url(https://example.com/image.png)">Text</p>')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('remote page resource', result.stdout)

    def test_reading_links_and_embedded_image_are_allowed(self):
        result = self.check_site('<a href="https://example.com/reading">Reading</a>',
                                 'x{background:url(data:image/png;base64,AA==)}')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
