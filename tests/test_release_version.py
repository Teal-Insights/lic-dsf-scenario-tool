"""The package version and the stamped release version agree."""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class ReleaseVersion(unittest.TestCase):
    def test_versions_agree_and_are_a3(self):
        text = (ROOT / 'pyproject.toml').read_text(encoding='utf-8')
        version = re.search(r'^version = "([^"]+)"$', text, re.M).group(1)
        self.assertEqual(version, '0.1.0a3')
        release = ROOT / 'src' / 'lic_dsf' / 'release.py'
        if release.exists():  # absent only on the M2a fallback branch
            body = release.read_text(encoding='utf-8')
            self.assertEqual(re.search(r"^VERSION = '([^']+)'$", body, re.M).group(1), version)
            self.assertRegex(re.search(r"^RELEASE_DATE = '([^']+)'$", body, re.M).group(1), r'^2026-10-\d\d$')
