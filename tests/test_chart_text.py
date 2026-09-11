"""Atomic chart-text operation: legend labels and heading applied together or not at all."""
import copy
import json
import unittest
from pathlib import Path
import sqlite3
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from test_store import store

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lic_dsf import app


class ChartTextStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.s = store.ScenarioStore(Path(self.temp.name))
        self.sha = "a" * 64
        self.s.register_workbook(self.sha, "Local source")
        self.definition = {"delta_paths": {"11": [0.0, 1.0]}, "terms": None}
        self.identity = {"engine": "test", "version": "1"}
        self.control = self.s.save_scenario(self.sha, "Control name", self.definition, share_label="Control", shared_rationale={"11": "Kept note"})
        self.case = self.s.save_scenario(self.sha, "Case name", {"delta_paths": {"11": [0.0, 2.0]}, "terms": None}, share_label="Case")
        for scenario in (self.control, self.case):
            result = {"workbook_sha256": self.sha, "scenario": scenario["definition"], "scenario_hash": store.digest(scenario["definition"]),
                      "engine_identity": self.identity, "contract_version": "t", "points": [], "evidence": {}}
            self.s.record_run(scenario["id"], result, expected_revision=1)

    def tearDown(self):
        self.temp.cleanup()

    def tables(self):
        with sqlite3.connect(self.s.database) as db:
            return {t: list(db.execute(f"SELECT * FROM {t} ORDER BY rowid")) for t in ("scenarios", "revisions", "runs", "shared_rationale", "chart_context")}

    def current(self, sid):
        return self.s.current_run(sid, engine_identity=self.identity, contract_version="t")

    def test_labels_and_heading_apply_together_and_keep_calculations(self):
        out = self.s.save_chart_text(self.sha, [
            {"scenario_id": self.control["id"], "expected_revision": 1, "share_label": "Growth control"},
            {"scenario_id": self.case["id"], "expected_revision": 1, "share_label": "Lower growth"}],
            {"label": "Budget: FY2030/31"}, expected_context_revision=0)
        self.assertEqual(out["chart_context"], {"workbook_sha256": self.sha, "label": "Budget: FY2030/31", "revision": 1})
        self.assertEqual({s["id"]: (s["revision"], s["share_label"], s["name"]) for s in out["scenarios"]},
                         {self.control["id"]: (2, "Growth control", "Control name"), self.case["id"]: (2, "Lower growth", "Case name")})
        self.assertEqual(self.current(self.control["id"])["revision"], 2)
        self.assertEqual(self.current(self.control["id"])["shared_rationale"], {"11": "Kept note"})
        self.assertEqual(self.s.get_scenario(self.case["id"])["definition"], self.case["definition"])

    def test_unchanged_label_and_unchanged_heading_add_no_revision(self):
        out = self.s.save_chart_text(self.sha, [{"scenario_id": self.control["id"], "expected_revision": 1, "share_label": " Control "}], None, expected_context_revision=0)
        self.assertEqual(out["scenarios"][0]["revision"], 1)
        self.assertEqual(out["chart_context"]["revision"], 0)

    def test_invalid_heading_rolls_back_label_revisions(self):
        before = self.tables()
        for heading in ("https://example.invalid/brief", "W" * 81, "C:\\budget"):
            with self.subTest(heading=heading), self.assertRaises(ValueError):
                self.s.save_chart_text(self.sha, [{"scenario_id": self.control["id"], "expected_revision": 1, "share_label": "Renamed"}],
                                       {"label": heading}, expected_context_revision=0)
            self.assertEqual(self.tables(), before)

    def test_one_stale_label_rolls_back_everything(self):
        self.s.save_scenario(self.sha, "Case name", self.case["definition"], scenario_id=self.case["id"], expected_revision=1, share_label="Case v2")
        before = self.tables()
        with self.assertRaisesRegex(store.StaleResult, "another tab"):
            self.s.save_chart_text(self.sha, [
                {"scenario_id": self.control["id"], "expected_revision": 1, "share_label": "Renamed control"},
                {"scenario_id": self.case["id"], "expected_revision": 1, "share_label": "Renamed case"}],
                {"label": "Heading"}, expected_context_revision=0)
        self.assertEqual(self.tables(), before)

    def test_stale_context_revision_rolls_back_labels(self):
        self.s.seed_chart_context(self.sha, "Changed elsewhere")
        before = self.tables()
        with self.assertRaisesRegex(store.StaleResult, "chart context changed"):
            self.s.save_chart_text(self.sha, [{"scenario_id": self.control["id"], "expected_revision": 1, "share_label": "Renamed"}], None, expected_context_revision=0)
        self.assertEqual(self.tables(), before)

    def test_final_label_set_is_validated_and_swaps_are_accepted(self):
        before = self.tables()
        with self.assertRaisesRegex(ValueError, "share the legend label"):
            self.s.save_chart_text(self.sha, [{"scenario_id": self.control["id"], "expected_revision": 1, "share_label": "case"}], None, expected_context_revision=0)
        self.assertEqual(self.tables(), before)
        out = self.s.save_chart_text(self.sha, [
            {"scenario_id": self.control["id"], "expected_revision": 1, "share_label": "Case"},
            {"scenario_id": self.case["id"], "expected_revision": 1, "share_label": "Control"}], None, expected_context_revision=0)
        self.assertEqual({s["id"]: s["share_label"] for s in out["scenarios"]}, {self.control["id"]: "Case", self.case["id"]: "Control"})
        self.assertEqual(self.current(self.control["id"])["share_label"], "Case")

    def test_invalid_labels_refused_before_any_write(self):
        before = self.tables()
        for label in ("", "x" * 41, "Reference baseline", "reference BASELINE", "/tmp/x", "C:x", "https://x", "a\x00b"):
            with self.subTest(label=label), self.assertRaises(ValueError):
                self.s.save_chart_text(self.sha, [{"scenario_id": self.control["id"], "expected_revision": 1, "share_label": label}], {"label": "Fine"}, expected_context_revision=0)
            self.assertEqual(self.tables(), before)
        for bad in ("not a list", [{"scenario_id": self.control["id"], "expected_revision": "1", "share_label": "x"}],
                    [{"scenario_id": self.control["id"], "expected_revision": 1}], [{"scenario_id": "nope", "expected_revision": 1, "share_label": "x"}]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.s.save_chart_text(self.sha, bad, None, expected_context_revision=0)
        self.assertEqual(self.tables(), before)

    def test_other_workbook_scenario_refused(self):
        other = "b" * 64
        self.s.register_workbook(other, "Other")
        foreign = self.s.save_scenario(other, "Foreign", self.definition, share_label="Foreign")
        before = self.tables()
        with self.assertRaises(ValueError):
            self.s.save_chart_text(self.sha, [{"scenario_id": foreign["id"], "expected_revision": 1, "share_label": "Moved"}], None, expected_context_revision=0)
        self.assertEqual(self.tables(), before)


class ChartTextApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = app.Workspace(SimpleNamespace(data_dir=self.temp.name, calculation_lock=None))
        self.sha = "a" * 64
        self.workspace.store.register_workbook(self.sha, "INTERNAL_SOURCE_SENTINEL.xlsx")
        definition = {"delta_paths": {"11": [0.0, 1.0]}, "terms": None}
        self.case = self.workspace.store.save_scenario(self.sha, "INTERNAL_CASE_SENTINEL", definition, share_label="Growth")

    def tearDown(self):
        self.workspace.executor.shutdown(wait=True)
        self.temp.cleanup()

    def post(self, route, payload):
        from io import BytesIO
        body = json.dumps(payload).encode()
        handler = object.__new__(app.handler_for(self.workspace))
        handler.path = route
        handler.headers = {"Content-Length": str(len(body)), "Host": "127.0.0.1:12345", "X-DSF-Token": self.workspace.token}
        handler.server = SimpleNamespace(server_port=12345)
        handler.connection = SimpleNamespace(settimeout=lambda _: None)
        handler.rfile = BytesIO(body)
        answers = []
        handler.send = lambda *args: answers.append(args)
        handler.do_POST()
        return answers[0]

    def records(self):
        with sqlite3.connect(self.workspace.store.database) as db:
            return {t: list(db.execute(f"SELECT * FROM {t} ORDER BY rowid")) for t in ("scenarios", "revisions", "chart_context", "shared_rationale")}

    def test_route_applies_atomically_and_maps_conflicts(self):
        request = {"workbook_sha": self.sha, "labels": [{"scenario_id": self.case["id"], "expected_revision": 1, "share_label": "Lower growth"}],
                   "heading": {"label": "Illustrative growth sensitivity"}, "expected_context_revision": 0}
        status, out = self.post("/api/chart-text", request)
        self.assertEqual(status, 200)
        self.assertEqual(out["chart_context"]["revision"], 1)
        self.assertEqual(out["scenarios"][0]["revision"], 2)
        self.assertNotIn("INTERNAL_SOURCE", json.dumps(out))
        before = self.records()
        status, error = self.post("/api/chart-text", dict(request, expected_context_revision=0))
        self.assertEqual(status, 409)
        self.assertIn("Reload", error["error"])
        self.assertEqual(self.records(), before)
        status, error = self.post("/api/chart-text", dict(request, expected_context_revision=1, heading={"label": "https://example.invalid"}))
        self.assertEqual(status, 400)
        self.assertEqual(self.records(), before)
        status, error = self.post("/api/chart-text", dict(request, expected_context_revision=1))
        self.assertEqual(status, 400)
        self.assertIn("another tab", error["error"])
        self.assertEqual(self.records(), before)
        self.assertEqual(self.post("/api/chart-text", {"workbook_sha": self.sha, "labels": []})[0], 400)
        self.assertEqual(self.post("/api/chart-text", dict(request, extra=True))[0], 400)


if __name__ == "__main__":
    unittest.main()
