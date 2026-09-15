"""Exercise Git's CRLF checkout conversion without changing the source checkout."""
import hashlib
from importlib.resources import files
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


class ResourceCheckoutTests(unittest.TestCase):
    def test_windows_style_checkout_preserves_teaching_resource_bytes(self):
        root = Path(__file__).resolve().parents[1]
        env = {key: value for key, value in os.environ.items()
               if not key.startswith('GIT_')}
        env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
        with tempfile.TemporaryDirectory() as temporary:
            scratch = Path(temporary)

            def git(*args):
                return subprocess.run(
                    ['git', '-C', str(scratch), *args], env=env, check=True,
                    capture_output=True, timeout=30,
                )

            git('init')
            git('config', 'core.autocrlf', 'true')
            git('config', 'core.eol', 'crlf')
            (scratch / '.gitattributes').write_bytes((root / '.gitattributes').read_bytes())
            expected = {}
            resources = files('lic_dsf').joinpath('illustrative_cases')
            for resource in resources.iterdir():
                if resource.name.endswith('.json'):
                    name = 'src/lic_dsf/illustrative_cases/' + resource.name
                    raw = resource.read_bytes()
                    self.assertNotIn(b'\r', raw)
                    target = scratch / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(raw)
                    expected[name] = hashlib.sha256(raw).hexdigest()
            self.assertEqual(len(expected), 3)
            # A control file proves checkout actually exercised CRLF conversion.
            (scratch / 'unprotected.txt').write_bytes(b'first line\nsecond line\n')
            git('add', '.gitattributes', 'src', 'unprotected.txt')
            checkout = scratch / 'checked-out'
            git('checkout-index', '--all', '--prefix=' + checkout.as_posix() + '/')
            self.assertEqual((checkout / 'unprotected.txt').read_bytes(),
                             b'first line\r\nsecond line\r\n')
            for name, digest in expected.items():
                with self.subTest(resource=name):
                    self.assertEqual(hashlib.sha256((checkout / name).read_bytes()).hexdigest(),
                                     digest)


if __name__ == '__main__':
    unittest.main()
