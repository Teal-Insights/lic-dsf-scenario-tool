"""Synthetic HTTP contract tests; no workbook, network service or calculation fixture."""
from contextlib import closing
from io import BytesIO
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lic_dsf import app
from lic_dsf.store import digest


class ContextApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = app.Workspace(SimpleNamespace(data_dir=self.temp.name, calculation_lock=None))
        self.sha = "a" * 64
        self.identity = {"engine": "synthetic", "version": "1"}
        self.workspace.store.register_workbook(self.sha, "INTERNAL_SOURCE_SENTINEL.xlsx")
        definition = {"delta_paths": {"11": [0.0, 1.0]}, "terms": None}
        case = self.workspace.store.save_scenario(self.sha, "INTERNAL_CASE_SENTINEL", definition, share_label="Growth")
        self.sid = case["id"]
        result = {"workbook_sha256": self.sha, "contract_version": app.CONTRACT_VERSION,
                  "engine_identity": self.identity, "scenario": definition, "scenario_hash": digest(definition),
                  "first_projection_year": 2030, "input_years": [2030, 2031], "points": [],
                  "thresholds": {}, "evidence": {"calculation": "computed_unverified", "live_excel": "pending"},
                  "warnings": [], "internal_path": "INTERNAL_PATH_SENTINEL"}
        self.workspace.store.record_run(self.sid, result, expected_revision=1)
        self.workspace.store.add_reasoning(self.sid, "INTERNAL_REASONING_SENTINEL")
        self.request = {"scenario_ids": [self.sid], "comparator_id": self.sid,
                        "workbook_sha": self.sha, "expected_chart_context_revision": 0}
        self.identity_patch = patch.object(app, "engine_identity", return_value=self.identity)
        self.identity_patch.start()

    def tearDown(self):
        self.identity_patch.stop()
        self.workspace.executor.shutdown(wait=True)
        self.temp.cleanup()

    def post(self, route, payload):
        """Exercise the actual handler without binding a listening socket."""
        body = json.dumps(payload).encode()
        handler = object.__new__(app.handler_for(self.workspace))
        handler.path = route
        handler.headers = {"Content-Length": str(len(body)), "Host": "127.0.0.1:12345",
                           "X-DSF-Token": self.workspace.token}
        handler.server = SimpleNamespace(server_port=12345)
        handler.connection = SimpleNamespace(settimeout=lambda _: None)
        handler.rfile = BytesIO(body)
        answers = []
        handler.send = lambda *args: answers.append(args)
        handler.do_POST()
        self.assertEqual(len(answers), 1)
        return answers[0]

    def records(self):
        with closing(sqlite3.connect(self.workspace.store.database)) as db, db:
            return {table: list(db.execute(f"SELECT * FROM {table} ORDER BY rowid"))
                    for table in ("workbooks", "scenarios", "revisions", "runs", "reasoning")}

    def test_save_compare_export_clear_without_numerical_changes(self):
        before = self.records()
        old = self.post("/api/compare", self.request)[1]
        status, context = self.post("/api/chart-context", {"workbook_sha": self.sha,
            "label": "Budget: FY2030/31", "expected_revision": 0})
        self.assertEqual(status, 200)
        self.assertEqual(context["revision"], 1)
        request = dict(self.request, expected_chart_context_revision=1)
        status, comparison = self.post("/api/compare", request)
        self.assertEqual(status, 200)
        self.assertEqual(comparison["format"], "lic-dsf-comparison-v3")
        self.assertEqual(comparison["chart_context"], context)
        self.assertEqual(comparison["runs"], old["runs"])
        exported = self.post("/api/export", dict(request, format="json"))
        self.assertEqual(exported[0], 200)
        self.assertEqual(json.loads(exported[1]), comparison)
        self.assertNotIn("INTERNAL_", json.dumps(comparison))
        self.assertEqual(set(comparison), {"format", "workbook_sha256", "chart_context", "comparator_id", "runs", "workbook_provenance"})
        self.assertEqual(set(comparison["chart_context"]), {"workbook_sha256", "label", "revision"})
        cleared = self.post("/api/chart-context", {"workbook_sha": self.sha, "label": None, "expected_revision": 1})
        self.assertEqual(cleared[1]["revision"], 2)
        self.assertIsNone(cleared[1]["label"])
        self.assertEqual(self.records(), before)

    def test_conflicting_context_save_comparison_and_export_return_409(self):
        self.workspace.store.seed_chart_context(self.sha, "Changed elsewhere")
        for route, request in (("/api/chart-context", {"workbook_sha": self.sha, "label": "Draft", "expected_revision": 0}),
                               ("/api/compare", self.request), ("/api/export", dict(self.request, format="json"))):
            with self.subTest(route=route):
                response = self.post(route, request)
                self.assertEqual(response[0], 409)
                self.assertIn("Reload", response[1]["error"])
        self.assertEqual(self.workspace.store.get_chart_context(self.sha)["label"], "Changed elsewhere")
        # Both nulls must not invoke the store's legacy internal omitted-pair API.
        for route in ("/api/compare", "/api/export"):
            response = self.post(route, dict(self.request, workbook_sha=None, expected_chart_context_revision=None))
            self.assertEqual(response[0], 400)
            self.assertNotIn("Changed elsewhere", json.dumps(response))

    def test_missing_source_or_revision_and_client_caption_overrides_rejected(self):
        for route in ("/api/compare", "/api/export"):
            for field in ("workbook_sha", "expected_chart_context_revision"):
                payload = dict(self.request); del payload[field]
                response = self.post(route, payload)
                self.assertEqual(response[0], 400)
                self.assertIn("Reload", response[1]["error"])
            for field in ("chart_context", "label", "workbook_provenance"):
                response = self.post(route, dict(self.request, **{field: "UNTRUSTED_SENTINEL"}))
                self.assertEqual(response[0], 400)
                self.assertNotIn("UNTRUSTED_SENTINEL", json.dumps(response))
        for invalid in (None, True, -1, "0"):
            self.assertEqual(self.post("/api/compare", dict(self.request, expected_chart_context_revision=invalid))[0], 400)

    def test_bad_context_never_echoed_and_other_source_not_exported(self):
        for label in ("C:INTERNAL_SENTINEL", "https://example.invalid/INTERNAL_SENTINEL", "x\nINTERNAL_SENTINEL", ["INTERNAL_SENTINEL"]):
            response = self.post("/api/chart-context", {"workbook_sha": self.sha, "label": label, "expected_revision": 0})
            self.assertEqual(response[0], 400)
            self.assertNotIn("INTERNAL_SENTINEL", json.dumps(response))
        self.assertEqual(self.post("/api/compare", dict(self.request, workbook_sha="b" * 64))[0], 400)
        self.assertEqual(self.post("/api/chart-context", {"workbook_sha": self.sha, "label": "Valid", "expected_revision": 0, "extra": True})[0], 400)
        self.assertEqual(self.post("/api/chart-context", ["bad"])[0], 400)

    def get(self, route):
        handler = object.__new__(app.handler_for(self.workspace))
        handler.path = route
        handler.headers = {"Host": "127.0.0.1:12345", "X-DSF-Token": self.workspace.token}
        handler.server = SimpleNamespace(server_port=12345)
        answers = []
        handler.send = lambda *args: answers.append(args)
        handler.do_GET()
        self.assertEqual(len(answers), 1)
        return answers[0]

    def test_label_only_revision_keeps_results_current_for_compare_and_export(self):
        case = self.workspace.store.get_scenario(self.sid)
        before = self.post("/api/compare", self.request)[1]
        with patch.object(self.workspace, "path", return_value=Path("synthetic.xlsx")), \
             patch.object(app, "inspect_workbook", return_value={"input_years": [2030, 2031]}), \
             patch.object(app, "normalize_scenario", side_effect=lambda definition, years: definition):
            status, saved = self.post("/api/save", {"workbook_sha": self.sha, "name": "INTERNAL_RENAMED_SENTINEL",
                "share_label": "Revised", "definition": case["definition"], "scenario_id": self.sid, "expected_revision": 1,
                "shared_rationale": {"11": "Revenue effort assumed."}})
        self.assertEqual(status, 200)
        self.assertEqual(saved["revision"], 2)
        status, loaded = self.get("/api/scenario?id=" + self.sid)
        self.assertEqual(status, 200)
        self.assertEqual(loaded["run"]["revision"], 2)
        self.assertEqual(loaded["run"]["result"]["evidence"]["calculation"], "computed_unverified")
        status, comparison = self.post("/api/compare", self.request)
        self.assertEqual(status, 200)
        run = comparison["runs"][0]
        self.assertEqual((run["revision"], run["share_label"]), (2, "Revised"))
        self.assertEqual(run["shared_rationale"], {"11": "Revenue effort assumed."})
        self.assertEqual(run["result"], before["runs"][0]["result"])
        self.assertEqual(run["result_hash"], before["runs"][0]["result_hash"])
        exported = self.post("/api/export", dict(self.request, format="json"))
        self.assertEqual(exported[0], 200)
        self.assertNotIn("INTERNAL_", exported[1].decode())

    def test_context_does_not_make_stale_numerical_results_current(self):
        # A numerical change (not a label-only revision) makes the saved result stale.
        self.workspace.store.save_scenario(self.sha, "Revision", {"delta_paths": {"11": [0.0, 2.0]}, "terms": None},
                                           scenario_id=self.sid, expected_revision=1, share_label="Revised")
        self.workspace.store.seed_chart_context(self.sha, "New label")
        for route in ("/api/compare", "/api/export"):
            self.assertEqual(self.post(route, dict(self.request, expected_chart_context_revision=1))[0], 400)

    def test_workbook_context_includes_only_explicit_saved_label(self):
        fake_book = SimpleNamespace(close=lambda: None)
        inspection = {"workbook_sha256": self.sha, "first_projection_year": 2030}
        with patch.object(self.workspace, "path", return_value=Path("synthetic.xlsx")), \
             patch.object(app, "inspect_workbook", return_value=inspection), \
             patch.object(app, "imported_scenario", return_value={}), \
             patch.object(app, "zero_scenario", return_value={}), \
             patch("lic_dsf.ida21.METRICS", []), \
             patch("openpyxl.load_workbook", return_value=fake_book):
            self.assertIsNone(self.workspace.context(self.sha)["chart_context"]["label"])
            saved = self.workspace.store.seed_chart_context(self.sha, "Deliberate label")
            self.assertEqual(self.workspace.context(self.sha)["chart_context"], saved)


if __name__ == "__main__":
    unittest.main()
