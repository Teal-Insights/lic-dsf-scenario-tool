"""A shifted projection year must match Excel on every sampled probe.

The workbook is the Excel-recalculated public converter output. It is
gitignored. DSF_SHIFTED_WORKBOOK selects the file when a run must compare
against that workbook. Otherwise a local copy is used when one is already
present, or the test downloads PUBLIC_REPRO_DRIVE_LINK into tests/fixtures.
Without a workbook and without that link the test is skipped. A present
workbook that disagrees with Excel still fails at the locked tolerance.
"""
import os
import re
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path
import unittest

from lic_dsf.compare import ATOL
from lic_dsf.engine import calculate
from lic_dsf.ida21 import probes

FIXTURES = Path(__file__).resolve().parent / 'fixtures'
WORKBOOK_NAME = '2026-11-16_public-repro_converter-output_calc-fails.xlsm'
FIXTURE = FIXTURES / WORKBOOK_NAME
ROOT_COPY = FIXTURES.parent.parent / WORKBOOK_NAME
LINK_VARIABLE = 'PUBLIC_REPRO_DRIVE_LINK'
_MIN_BYTES = 1_000_000


def _present(path):
    return path.is_file() and path.stat().st_size >= _MIN_BYTES


def _local_workbook():
    for path in (FIXTURE, ROOT_COPY):
        if _present(path):
            return path
    return None


def _drive_file_id(url):
    match = re.search(r'/file/d/([^/?#]+)', url) or re.search(r'[?&]id=([^&]+)', url)
    if not match:
        raise ValueError(f'{LINK_VARIABLE} is not a Google Drive file link')
    return match.group(1)


def _fetch(opener, url):
    with opener.open(url, timeout=180) as response:
        return response.read()


def _confirm_token(payload, jar):
    for cookie in jar:
        if cookie.name.startswith('download_warning') and cookie.value:
            return cookie.value
    text = payload.decode('utf-8', 'replace')
    match = re.search(r'name="confirm" value="([^"]+)"', text) or re.search(
        r'confirm=([0-9A-Za-z_\-]+)', text
    )
    return match.group(1) if match else 't'


def _download_drive(url, dest):
    file_id = urllib.parse.quote(_drive_file_id(url.strip()))
    jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    opener.addheaders = [('User-Agent', 'lic-dsf-scenario-tool-tests')]
    first = f'https://drive.google.com/uc?export=download&id={file_id}'
    payload = _fetch(opener, first)
    if not payload.startswith(b'PK'):
        token = urllib.parse.quote(_confirm_token(payload, jar))
        confirmed = f'https://drive.google.com/uc?export=download&confirm={token}&id={file_id}'
        payload = _fetch(opener, confirmed)
    if not payload.startswith(b'PK'):
        direct = (
            'https://drive.usercontent.google.com/download'
            f'?id={file_id}&export=download&confirm=t'
        )
        payload = _fetch(opener, direct)
    if not payload.startswith(b'PK') or len(payload) < _MIN_BYTES:
        if b'accounts.google.com' in payload:
            raise RuntimeError(f'{LINK_VARIABLE} did not return the workbook; Google Drive asked for a sign-in')
        raise RuntimeError(f'{LINK_VARIABLE} did not return the Excel workbook')
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_suffix('.xlsm.partial')
    partial.write_bytes(payload)
    partial.replace(dest)
    return dest


def _workbook():
    override = os.environ.get('DSF_SHIFTED_WORKBOOK', '').strip()
    if override:
        return Path(override)
    found = _local_workbook()
    if found is not None:
        return found
    link = os.environ.get(LINK_VARIABLE, '').strip()
    if not link:
        return None
    return _download_drive(link, FIXTURE)


class ShiftedProjectionProbes(unittest.TestCase):
    maxDiff = None

    def test_every_probe_matches_excel(self):
        self.assertEqual(ATOL, 1e-6)
        self.assertEqual(len(probes()), 76)
        path = _workbook()
        if path is None:
            self.skipTest(
                f'{LINK_VARIABLE} is not set, and the public repro workbook is not available'
            )
        self.assertTrue(
            _present(path),
            f'Excel-recalculated workbook is required: {path}',
        )
        evidence = calculate(path)['evidence']
        self.assertEqual(evidence['cache_total'], 76)
        mismatches = evidence['cache_mismatch_probes']
        self.assertEqual(
            mismatches,
            [],
            f"{evidence['cache_passed']} of {evidence['cache_total']} probes matched Excel at {ATOL}",
        )
        self.assertEqual(evidence['cache_passed'], 76)
        self.assertEqual(evidence['saved_cache'], 'matched')


if __name__ == '__main__':
    unittest.main()
