"""Exercise worker IPC under a non-UTF-8 default, without workbook evaluation."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


class WorkerEncodingTests(unittest.TestCase):
    def test_non_ascii_workbook_path_survives_locale_independent_request(self):
        source = Path(__file__).resolve().parents[1] / 'src'
        with tempfile.TemporaryDirectory(prefix='lic-dsf-encoding-') as folder:
            request = Path(folder) / 'request.json'
            workbook = 'analysis/\u00e9conomie-\u4e2d\u6587.xlsm'
            request.write_text(json.dumps({
                'workbook': workbook, 'workbook_sha256': 'a' * 64,
                'scenario': {'label': '\u00e9conomie'},
                'parent_pid': os.getpid(), 'deadline_utc': time.time() + 30,
            }, ensure_ascii=False), encoding='utf-8')
            code = r'''
import json, locale, sys
from pathlib import Path
import lic_dsf
from lic_dsf import worker
request = Path(sys.argv[1])
# Establish whether the host gives this subprocess a non-UTF-8 default.
default = locale.getencoding()
if default.lower().replace('-', '') == 'utf8':
    raise SystemExit(77)
def calculate(workbook, scenario, expected_sha256):
    assert workbook == 'analysis/\u00e9conomie-\u4e2d\u6587.xlsm'
    assert scenario['label'] == '\u00e9conomie'
    assert expected_sha256 == 'a' * 64
    return {'workbook': workbook, 'label': scenario['label']}
lic_dsf.calculate = calculate
raise SystemExit(worker.main(request))
'''
            env = dict(os.environ, LC_ALL='C', LANG='C', PYTHONUTF8='0',
                       PYTHONCOERCECLOCALE='0', PYTHONPATH=str(source),
                       PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1')
            run = subprocess.run([sys.executable, '-X', 'utf8=0', '-c', code, str(request)],
                                 env=env, capture_output=True, timeout=30)
            if run.returncode == 77:
                self.skipTest('Host cannot supply a non-UTF-8 default locale for this check.')
            error = (Path(folder) / 'error.json')
            self.assertEqual(run.returncode, 0, (run.stderr.decode('utf-8', errors='replace'),
                             error.read_text(encoding='utf-8') if error.exists() else ''))
            result = json.loads((Path(folder) / 'result.json').read_text(encoding='utf-8'))
            self.assertEqual(result, {'workbook': workbook, 'label': '\u00e9conomie'})


if __name__ == '__main__':
    unittest.main()
