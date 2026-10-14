"""Text files under src are read and written as UTF-8, whatever the platform's default encoding."""
import ast
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODE = re.compile(r'^[rwxabt+]+$')


def mode_of(call, index):
    """The constant mode of an open-like call, '' when absent, None when not a constant."""
    for keyword in call.keywords:
        if keyword.arg == 'mode':
            return keyword.value.value if isinstance(keyword.value, ast.Constant) else None
    if len(call.args) > index:
        value = call.args[index]
        return value.value if isinstance(value, ast.Constant) and isinstance(value.value, str) else None
    return ''


def default_encoding_calls(tree):
    """Calls that would decode or encode text with the locale default (cp1252 on Windows)."""
    for call in ast.walk(tree):
        if not isinstance(call, ast.Call) or any(k.arg == 'encoding' for k in call.keywords):
            continue
        func = call.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, 'id', None)
        if name in ('read_text', 'write_text'):
            # importlib.metadata's Distribution.read_text takes a file name and is always UTF-8.
            receiver = getattr(func, 'value', None)
            if not (isinstance(receiver, ast.Call) and getattr(receiver.func, 'id', None) == 'distribution'):
                yield call
        elif name == 'open' and (isinstance(func, ast.Name) or getattr(func.value, 'id', None) == 'io') or name == 'fdopen':
            mode = mode_of(call, 1)
            if mode is None or 'b' not in mode:
                yield call
        elif name == 'open':
            # Path.open(mode): other .open(...) calls (webbrowser, urllib openers) take no mode.
            mode = mode_of(call, 0)
            if not call.args and not call.keywords or mode and MODE.match(mode) and 'b' not in mode:
                yield call


class TextEncodingTests(unittest.TestCase):
    def test_src_text_io_names_an_encoding(self):
        found = []
        for path in sorted((ROOT / 'src').rglob('*.py')):
            tree = ast.parse(path.read_text(encoding='utf-8'))
            found += [f'{path.relative_to(ROOT).as_posix()}:{c.lineno}: {ast.unparse(c)[:80]}'
                      for c in default_encoding_calls(tree)]
        self.assertEqual(found, [], 'text I/O without encoding= depends on the platform default')

    def test_guard_sees_default_encoding_calls(self):
        tree = ast.parse("p.read_text()\np.write_text(s)\nopen(f)\nopen(f, 'w')\nos.fdopen(d, 'w')\np.open()\n"
                         "p.open('a')\np.read_text(encoding='utf-8')\nopen(f, 'rb')\np.open('a+b')\n"
                         "webbrowser.open(url)\nopener.open(r, timeout=2)\ndistribution('x').read_text('y')\n")
        self.assertEqual([c.lineno for c in default_encoding_calls(tree)], [1, 2, 3, 4, 5, 6, 7])

    def test_hosted_page_is_the_same_under_a_non_utf8_default(self):
        from lic_dsf.hosted import hosted_page
        code = r'''
import hashlib, locale
if locale.getencoding().lower().replace('-', '') == 'utf8':
    raise SystemExit(77)
from lic_dsf.hosted import hosted_page
print(hashlib.sha256(hosted_page()).hexdigest())
'''
        env = dict(os.environ, LC_ALL='C', LANG='C', PYTHONUTF8='0', PYTHONCOERCECLOCALE='0',
                   PYTHONPATH=str(ROOT / 'src'), PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1')
        run = subprocess.run([sys.executable, '-X', 'utf8=0', '-c', code], env=env, capture_output=True, timeout=60)
        if run.returncode == 77:
            self.skipTest('Host cannot supply a non-UTF-8 default locale for this check.')
        self.assertEqual(run.returncode, 0, run.stderr.decode('utf-8', errors='replace')[-2000:])
        self.assertEqual(run.stdout.decode('ascii').strip(), hashlib.sha256(hosted_page()).hexdigest())


if __name__ == '__main__':
    unittest.main()
