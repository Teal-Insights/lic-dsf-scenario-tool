import hashlib
import io
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch, Mock

from lic_dsf import official_example as official
from lic_dsf.app import Workspace


class Response(io.BytesIO):
    status = 200
    headers = {}


class OfficialDownloadTests(unittest.TestCase):
    def download(self, payload, headers=None):
        response = Response(payload)
        response.headers = headers or {}
        opener = Mock()
        opener.open.return_value = response
        with patch.object(official.urllib.request, "build_opener", return_value=opener):
            result = official.download_official_example()
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, official.OFFICIAL_EXAMPLE_URL)
        self.assertIsNone(request.data)
        return result

    def test_only_verified_bytes_returned(self):
        data = b"neutral test workbook bytes"
        with patch.object(official, "OFFICIAL_EXAMPLE_BYTES", len(data)), patch.object(official, "OFFICIAL_EXAMPLE_SHA", hashlib.sha256(data).hexdigest()):
            self.assertEqual(self.download(data), data)
            with self.assertRaisesRegex(ValueError, "match"):
                self.download(b"x" * len(data))
            with self.assertRaises(ValueError):
                self.download(data + b"x")
            with self.assertRaises(ValueError):
                self.download(data, {"Content-Length": str(len(data) + 1)})

    def test_network_failure_is_actionable_and_no_private_detail(self):
        opener = Mock()
        opener.open.side_effect = OSError("sensitive test path")
        with patch.object(official.urllib.request, "build_opener", return_value=opener):
            with self.assertRaises(ValueError) as result:
                official.download_official_example()
        self.assertIn("internet connection", str(result.exception))
        self.assertNotIn("sensitive test path", str(result.exception))

    def test_redirects_cannot_leave_secure_publisher_origin(self):
        redirect = official._PublisherRedirect()
        req = official.urllib.request.Request(official.OFFICIAL_EXAMPLE_URL)
        for url in ["https://example.org/template", "http://thedocs.worldbank.org/template", "https://user@thedocs.worldbank.org/template", "https://thedocs.worldbank.org:444/template"]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                redirect.redirect_request(req, None, 302, "Found", {}, url)

    def test_download_is_explicit_and_cached_reuse_needs_no_network(self):
        with tempfile.TemporaryDirectory() as directory:
            args = SimpleNamespace(data_dir=directory, calculation_lock=None, example=None)
            with patch("lic_dsf.app.download_official_example") as fetch:
                workspace = Workspace(args)
                fetch.assert_not_called()
                try:
                    data = b"verified cache stand-in"
                    cached = workspace.uploads / (official.OFFICIAL_EXAMPLE_SHA + ".xlsm")
                    cached.write_bytes(data)
                    with patch("lic_dsf.app.verify_official_example", return_value=data) as verify, patch.object(workspace, "ingest", return_value={"accepted": True}) as ingest:
                        self.assertTrue(workspace.load_example()["accepted"])
                    verify.assert_called_once_with(data)
                    ingest.assert_called_once_with(data, "Official illustrative example")
                    fetch.assert_not_called()
                    with patch("lic_dsf.app.verify_official_example", side_effect=ValueError("Changed cached file")):
                        with self.assertRaisesRegex(ValueError, "Changed"):
                            workspace.load_example()
                    self.assertEqual(cached.read_bytes(), data)
                    fetch.assert_not_called()
                    cached.unlink()
                    fetch.return_value = data
                    with patch.object(workspace, "ingest", return_value={"accepted": True}):
                        workspace.load_example()
                    fetch.assert_called_once_with()
                finally:
                    workspace.executor.shutdown(wait=True)


if __name__ == "__main__":
    unittest.main()
