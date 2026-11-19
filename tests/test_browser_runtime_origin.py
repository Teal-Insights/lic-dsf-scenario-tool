"""The in-browser runtime is loaded from this site, not from a third-party CDN."""
import http.client
import sys
import threading
import unittest
import urllib.error
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "poc" / "browser"))

import serve  # noqa: E402
from build_wheels import PYODIDE_INDEX  # noqa: E402


class RuntimeOriginTests(unittest.TestCase):
    def test_workers_and_manifest_use_the_site_runtime(self):
        self.assertEqual(PYODIDE_INDEX, "/pyodide/v314.0.7/full/")
        module = PYODIDE_INDEX + "pyodide.mjs"
        for name in ("worker.js", "app-worker.js"):
            text = (ROOT / "poc" / "browser" / name).read_text(encoding="utf-8")
            self.assertIn(f'from "{module}"', text)
            self.assertIn("packageBaseUrl: pyodideIndex", text)
            self.assertNotIn("jsdelivr", text)
        builder = (ROOT / "poc" / "browser" / "build_wheels.py").read_text(encoding="utf-8")
        self.assertIn('"pyodide": PYODIDE_INDEX', builder)
        self.assertNotIn("jsdelivr", builder)


class _Response:
    def __init__(self, body, url, content_type="application/wasm", length=None):
        self._body = body
        self._url = url
        self.headers = {"Content-Type": content_type}
        if length is not None:
            self.headers["Content-Length"] = str(length)
        self.read_called = False

    def read(self):
        self.read_called = True
        return self._body

    def geturl(self):
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class RuntimeProxyTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(
            ("127.0.0.1", 0), partial(serve.Handler, directory=str(serve.HERE)))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def exchange(self, method, target):
        host, port = self.server.server_address
        connection = http.client.HTTPConnection(host, port, timeout=10)
        connection.request(method, target)
        response = connection.getresponse()
        body = response.read()
        headers = {key.lower(): value for key, value in response.getheaders()}
        status = response.status
        connection.close()
        return status, headers, body

    def test_runtime_file_is_read_from_the_public_site(self):
        payload = b"wasm-bytes"
        upstream = serve.PYODIDE_ORIGIN + PYODIDE_INDEX + "pyodide.asm.wasm"
        fake = _Response(payload, upstream, length=len(payload))
        with patch("urllib.request.urlopen", return_value=fake) as opened:
            status, headers, body = self.exchange("GET", PYODIDE_INDEX + "pyodide.asm.wasm")
        self.assertEqual(status, 200)
        self.assertEqual(body, payload)
        self.assertEqual(headers["content-type"], "application/wasm")
        self.assertEqual(headers["content-length"], str(len(payload)))
        request = opened.call_args.args[0]
        self.assertEqual(request.full_url, upstream)
        self.assertEqual(request.get_method(), "GET")

    def test_head_uses_the_upstream_length(self):
        upstream = serve.PYODIDE_ORIGIN + PYODIDE_INDEX + "pyodide.asm.wasm"
        fake = _Response(b"unused", upstream, length=11)
        with patch("urllib.request.urlopen", return_value=fake):
            status, headers, body = self.exchange("HEAD", PYODIDE_INDEX + "pyodide.asm.wasm?unused=1")
        self.assertEqual(status, 200)
        self.assertEqual(body, b"")
        self.assertEqual(headers["content-length"], "11")
        self.assertFalse(fake.read_called)

    def test_nested_runtime_path_is_not_fetched(self):
        with patch("urllib.request.urlopen") as opened:
            status, _, body = self.exchange("GET", PYODIDE_INDEX + "nested/pyodide.mjs")
        self.assertEqual(status, 404)
        self.assertEqual(body, b"Not found.")
        opened.assert_not_called()

    def test_foreign_redirect_is_refused(self):
        fake = _Response(b"foreign-secret", "https://evil.example/pyodide.mjs")
        with patch("urllib.request.urlopen", return_value=fake):
            status, _, body = self.exchange("GET", PYODIDE_INDEX + "pyodide.mjs")
        self.assertEqual(status, 502)
        self.assertNotIn(b"foreign-secret", body)
        self.assertIn(b"unavailable", body)

    def test_upstream_error_hides_the_response_body(self):
        def raise_error(request, timeout):
            raise urllib.error.HTTPError(request.full_url, 403, "denied", hdrs=None, fp=None)

        with patch("urllib.request.urlopen", side_effect=raise_error):
            status, _, body = self.exchange("GET", PYODIDE_INDEX + "missing.wasm")
        self.assertEqual(status, 502)
        self.assertNotIn(b"denied", body)
        self.assertIn(b"unavailable", body)
