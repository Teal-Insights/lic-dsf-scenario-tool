"""Route checks for the in-browser workspace. No Pyodide, external network or calculation."""
import http.client
import importlib.util
import json
import sys
import tempfile
import threading
import unittest
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "poc" / "browser"))


def load_session():
    spec = importlib.util.spec_from_file_location("browser_session", ROOT / "poc" / "browser" / "session.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


browser_session = load_session()
import serve  # noqa: E402


class BrowserSessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.session = browser_session.BrowserSession(self.temp.name)
        self.token = self.session.workspace.token

    def tearDown(self):
        self.temp.cleanup()

    def dispatch(self, method, target, body=b"", token=None):
        headers = {} if token is None else {"x-dsf-token": token}
        return self.session.dispatch(method, target, body, headers)

    def test_boot_shape_matches_the_page(self):
        status, content_type, body, extra = self.dispatch("GET", "/api/boot")
        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json")
        payload = json.loads(body)
        self.assertEqual(payload["token"], self.token)
        self.assertTrue(payload["example_available"])
        self.assertTrue(payload["illustrative_example"])
        self.assertTrue(payload["example_requires_download"])
        self.assertEqual(payload["workbooks"], [])
        self.assertIn("in this tab", payload["note"])
        self.assertIn("pending", payload["note"])
        self.assertFalse(extra["persist"])
        self.assertIsNone(extra["calculate"])

    def test_routes_require_the_boot_token(self):
        status, _, body, _ = self.dispatch("POST", "/api/save", b"{}", token="nope")
        self.assertEqual(status, 403)
        self.assertIn("Reload", json.loads(body)["error"])
        status, _, body, _ = self.dispatch("GET", "/api/job?id=missing", token="nope")
        self.assertEqual(status, 403)

    def test_empty_post_is_rejected(self):
        status, _, body, extra = self.dispatch("POST", "/api/example", b"", token=self.token)
        self.assertEqual(status, 413)
        self.assertFalse(extra["persist"])
        self.assertIn("empty", json.loads(body)["error"])

    def test_nonfinite_json_is_rejected(self):
        status, _, body, _ = self.dispatch("POST", "/api/save", b'{"value":NaN}', token=self.token)
        self.assertEqual(status, 400)
        self.assertEqual(json.loads(body)["error"], "Use finite numbers.")

    def test_unknown_scenario_does_not_start_a_job(self):
        status, _, body, extra = self.dispatch(
            "POST", "/api/calculate", b'{"scenario_id":"missing"}', token=self.token)
        self.assertEqual(status, 400)
        self.assertIsNone(extra["calculate"])
        self.assertIn("Scenario not found", json.loads(body)["error"])

    def test_a_second_calculation_waits(self):
        sha = "ab" * 32
        self.session.workspace.store.register_workbook(sha, "Synthetic workbook")
        (self.session.workspace.uploads / (sha + ".xlsm")).write_bytes(b"not a workbook")
        saved = self.session.workspace.store.save_scenario(
            sha, "Case", {"delta_paths": {"11": [0.0]}, "terms": None}, share_label="Case")
        body = json.dumps({"scenario_id": saved["id"]}).encode()
        status, _, payload, extra = self.dispatch("POST", "/api/calculate", body, token=self.token)
        self.assertEqual(status, 202)
        job_id = extra["calculate"]
        self.assertEqual(json.loads(payload)["job_id"], job_id)
        status, _, running, _ = self.dispatch("GET", "/api/job?id=" + job_id, token=self.token)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(running)["status"], "running")
        status, _, refused, extra = self.dispatch("POST", "/api/calculate", body, token=self.token)
        self.assertEqual(status, 400)
        self.assertIsNone(extra["calculate"])
        self.assertIn("already running", json.loads(refused)["error"])
        self.session.run_calculation(job_id)
        _, _, finished, _ = self.dispatch("GET", "/api/job?id=" + job_id, token=self.token)
        self.assertEqual(json.loads(finished)["status"], "failed")
        self.assertNotIn("/", json.loads(finished)["message"])

    def test_bad_staged_example_is_not_cached(self):
        staged = Path(self.temp.name) / "staged.xlsm"
        staged.write_bytes(b"not the official template")
        self.session.official_stage = staged
        status, _, body, extra = self.dispatch("POST", "/api/example", b"{}", token=self.token)
        self.assertEqual(status, 400)
        self.assertFalse(extra["persist"])
        self.assertIn("official file", json.loads(body)["error"])
        self.assertFalse(staged.exists())
        self.assertFalse(self.session.official_example_cached())

    def test_path_errors_do_not_echo_paths(self):
        status, _, body = browser_session.BrowserSession._refuse(ValueError("see /tmp/private.xlsm"))
        self.assertEqual(status, 400)
        self.assertNotIn("/tmp", json.loads(body)["error"])

    def test_copy_fallback_preserves_an_existing_file(self):
        source = Path(self.temp.name) / "source"
        destination = Path(self.temp.name) / "destination"
        source.write_bytes(b"new")
        destination.write_bytes(b"old")
        with patch.object(browser_session, "_HARDLINK", side_effect=OSError("unsupported")):
            with self.assertRaises(OSError):
                browser_session.link_or_copy(source, destination)
        self.assertEqual(destination.read_bytes(), b"old")
        destination.unlink()
        with patch.object(browser_session, "_HARDLINK", side_effect=OSError("unsupported")):
            browser_session.link_or_copy(source, destination)
        self.assertEqual(destination.read_bytes(), b"new")

    def test_missing_hardlink_copies_bytes(self):
        source = Path(self.temp.name) / "source-bytes"
        destination = Path(self.temp.name) / "copied-bytes"
        source.write_bytes(b"abc")
        with patch.object(browser_session, "_HARDLINK", None):
            browser_session.link_or_copy(source, destination)
            destination.write_bytes(b"keep")
            with self.assertRaises(FileExistsError):
                browser_session.link_or_copy(source, destination)
        self.assertEqual(destination.read_bytes(), b"keep")

    def test_linux_workspace_keeps_hardlinks(self):
        self.assertTrue(browser_session.hardlinks_work(self.temp.name))
        self.assertTrue(browser_session.chmod_works(self.temp.name))
        self.assertTrue(browser_session.fsync_works(self.temp.name))

    def test_served_page_injects_the_bridge_without_editing_the_source(self):
        page = serve.application_page().decode()
        self.assertIn('<script src="/browser-bridge.js"></script>', page)
        self.assertIn('id="browserRuntime"', page)
        self.assertIn(">In-browser application<", page)
        self.assertIn('src:url(\'/fonts/Inter-Regular.otf\')', page)
        source = (ROOT / "src" / "lic_dsf" / "web.html").read_text(encoding="utf-8")
        self.assertNotIn("browser-bridge.js", source)
        self.assertIn(">Local workspace<", source)


class HeadMatchesGetTests(unittest.TestCase):
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
        result = response.status, headers, body
        connection.close()
        return result

    def assert_head_matches_get(self, target):
        status, headers, body = self.exchange("HEAD", target)
        get_status, get_headers, get_body = self.exchange("GET", target)
        self.assertEqual(status, get_status)
        self.assertEqual(headers["content-type"], get_headers["content-type"])
        self.assertEqual(headers["content-length"], get_headers["content-length"])
        self.assertEqual(int(headers["content-length"]), len(get_body))
        self.assertEqual(body, b"")

    def test_head_matches_the_generated_page_font_and_static_file(self):
        self.assert_head_matches_get("/")
        self.assert_head_matches_get("/app")
        self.assert_head_matches_get("/fonts/Inter-Regular.otf")
        self.assert_head_matches_get("/fonts/missing.otf")
        self.assert_head_matches_get("/index.html")
        status, _, body = self.exchange("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b">In-browser application<", body)
        page_length = len(body)
        _, _, index_body = self.exchange("GET", "/index.html")
        self.assertNotEqual(page_length, len(index_body))

    def test_head_official_example_reports_the_generated_bytes(self):
        payload = b"example-bytes"
        with patch.object(serve, "official_example_bytes", return_value=payload) as generated:
            status, headers, body = self.exchange("HEAD", "/official-example.xlsm")
            get_status, get_headers, get_body = self.exchange("GET", "/official-example.xlsm")
        self.assertEqual(generated.call_count, 2)
        self.assertEqual(status, 200)
        self.assertEqual(get_status, 200)
        self.assertEqual(body, b"")
        self.assertEqual(get_body, payload)
        self.assertEqual(headers["content-length"], str(len(payload)))
        self.assertEqual(headers["content-type"], get_headers["content-type"])
        self.assertEqual(headers["content-type"], "application/vnd.ms-excel.sheet.macroEnabled.12")


if __name__ == "__main__":
    unittest.main()
