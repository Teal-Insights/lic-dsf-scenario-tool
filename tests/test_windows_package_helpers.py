"""The Windows package helpers: the payload check in start_local.py and the CMD fallback."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

HELPERS = Path(__file__).resolve().parents[1] / 'packaging' / 'windows-package'


def load_start_local():
    spec = importlib.util.spec_from_file_location('start_local', HELPERS / 'start_local.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def package(folder, files):
    for name, data in files.items():
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    manifest = [{'path': n, 'sha256': hashlib.sha256(d).hexdigest(), 'bytes': len(d)} for n, d in sorted(files.items())]
    (folder / 'FILE-MANIFEST.json').write_text(json.dumps(manifest), encoding='utf-8')


class PayloadCheckTests(unittest.TestCase):
    def setUp(self):
        self.start_local = load_start_local()
        self.tmp = tempfile.TemporaryDirectory(prefix='lic-dsf-payload-')
        self.root = Path(self.tmp.name)
        package(self.root, {'start_local.py': b'x', 'runtime/python.exe': b'py', 'documentation/a.md': b'doc'})

    def tearDown(self):
        self.tmp.cleanup()

    def verify(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.start_local.verify_payload(self.root)
        return out.getvalue()

    def test_says_it_is_checking_before_hashing(self):
        self.assertEqual(self.verify().splitlines()[0], 'Checking package files...')

    def test_explorer_files_are_ignored(self):
        (self.root / 'Thumbs.db').write_bytes(b't')
        (self.root / 'documentation' / 'desktop.ini').write_bytes(b'd')
        (self.root / 'runtime' / 'Desktop.INI').write_bytes(b'd')
        self.verify()

    def test_extra_files_are_named_and_moved_out(self):
        for name in ('my workbook.xlsx', 'notes.txt', 'a.csv', 'b.csv', 'c.csv', 'd.csv'):
            (self.root / name).write_bytes(b'mine')
        with self.assertRaises(ValueError) as caught:
            self.verify()
        message = str(caught.exception)
        self.assertIn('Move these out of this folder, then start again.', message)
        self.assertNotIn('Extract a fresh', message)
        named = [n for n in ('a.csv', 'b.csv', 'c.csv', 'd.csv', 'my workbook.xlsx', 'notes.txt') if n in message]
        self.assertEqual(named, ['a.csv', 'b.csv', 'c.csv', 'd.csv', 'my workbook.xlsx'])
        self.assertIn('1 more', message)

    def test_missing_file_asks_for_a_fresh_copy(self):
        (self.root / 'documentation' / 'a.md').unlink()
        (self.root / 'mine.xlsx').write_bytes(b'mine')
        with self.assertRaisesRegex(ValueError, 'Extract a fresh complete copy'):
            self.verify()

    def test_changed_file_asks_for_a_fresh_copy(self):
        (self.root / 'runtime' / 'python.exe').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'Extract a fresh complete copy'):
            self.verify()


class FallbackTests(unittest.TestCase):
    def test_fallback_is_named_as_a_fallback(self):
        self.assertTrue((HELPERS / 'Start LIC-DSF (fallback).cmd').is_file())
        self.assertFalse((HELPERS / 'Start LIC-DSF.cmd').exists())

    def test_fallback_resolves_its_own_folder_and_points_to_the_signed_launcher(self):
        raw = (HELPERS / 'Start LIC-DSF (fallback).cmd').read_bytes()
        self.assertEqual(raw.count(b'\r\n'), raw.count(b'\n'))
        text = raw.decode('ascii')
        self.assertIn('"%~dp0runtime\\python.exe" -X utf8 -B "%~dp0start_local.py"', text)
        self.assertIn('cd /d "%~dp0"', text)
        self.assertIn('Start LIC-DSF (fallback).cmd could not find runtime\\python.exe', text)
        self.assertIn('Double-click Start LIC-DSF.exe inside that folder.', text)
        self.assertNotIn('Double-click Start LIC-DSF.cmd', text)


if __name__ == '__main__':
    unittest.main()
