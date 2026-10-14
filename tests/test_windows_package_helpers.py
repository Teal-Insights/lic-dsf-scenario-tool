"""The Windows package helpers: the payload check in start_local.py and the CMD fallback."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
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

    def test_lookalike_and_injected_files_still_block(self):
        for name in ('desktop.ini.py', 'Thumbs.db.dll', 'xdesktop.ini', 'runtime/evil.pth', 'runtime/pyvenv.cfg',
                     'runtime/Lib/site-packages/x.py', 'runtime/foo.dll', 'runtime/Lib/site-packages/Thumbs.db/evil.py'):
            with self.subTest(name=name), tempfile.TemporaryDirectory(prefix='lic-dsf-payload-') as folder:
                root = Path(folder)
                package(root, {'start_local.py': b'x', 'runtime/python.exe': b'py'})
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_bytes(b'planted')
                with self.assertRaises(ValueError) as caught, contextlib.redirect_stdout(io.StringIO()):
                    self.start_local.verify_payload(root)
                self.assertIn('Move these out of this folder', str(caught.exception))
                self.assertIn(name, str(caught.exception))

    def test_non_ascii_lookalike_still_blocks(self):
        name = 'des\u212atop.ini'  # KELVIN SIGN lower-cases to an ASCII k
        try:
            (self.root / name).write_bytes(b'planted')
        except (OSError, UnicodeError):
            self.skipTest('File system cannot hold this name.')
        if name not in os.listdir(self.root):
            self.skipTest('File system normalizes this name.')
        with self.assertRaisesRegex(ValueError, 'Move these out of this folder'):
            self.verify()

    def test_linked_explorer_file_is_refused(self):
        try:
            os.symlink(self.root / 'start_local.py', self.root / 'desktop.ini')
        except (OSError, NotImplementedError):
            self.skipTest('Symbolic links are unavailable here.')
        with self.assertRaisesRegex(ValueError, 'unexpected linked path'):
            self.verify()

    def test_says_it_is_checking_before_reporting_a_changed_file(self):
        (self.root / 'runtime' / 'python.exe').write_bytes(b'changed')
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(ValueError):
            self.start_local.verify_payload(self.root)
        self.assertEqual(out.getvalue().splitlines()[0], 'Checking package files...')


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

    def test_verify_script_runs_the_same_check_from_its_own_folder(self):
        raw = (HELPERS / 'Verify package.cmd').read_bytes()
        self.assertEqual(raw.count(b'\r\n'), raw.count(b'\n'))
        text = raw.decode('ascii')
        self.assertIn('cd /d "%~dp0"', text)
        self.assertIn('"%~dp0runtime\\python.exe" -X utf8 -B "%~dp0start_local.py" --verify-only', text)


if __name__ == '__main__':
    unittest.main()
