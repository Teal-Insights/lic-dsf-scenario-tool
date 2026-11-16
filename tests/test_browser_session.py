"""Route checks for the in-browser workspace. No Pyodide, network or calculation."""
import importlib.util
import json
import sys
import tempfile
import unittest
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
        self.assertIn(">In-browser proof of concept<", page)
        self.assertIn('src:url(\'/fonts/Inter-Regular.otf\')', page)
        source = (ROOT / "src" / "lic_dsf" / "web.html").read_text(encoding="utf-8")
        self.assertNotIn("browser-bridge.js", source)
        self.assertIn(">Local workspace<", source)


if __name__ == "__main__":
    unittest.main()
