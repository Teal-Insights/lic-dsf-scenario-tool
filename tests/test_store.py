import importlib.util
from pathlib import Path
import tempfile
import sys
import types
import unittest

# Exercise the standard-library store without importing the calculation runtime.
package = types.ModuleType("store_test_package")
package.__path__ = [str(Path(__file__).parents[1] / "src/lic_dsf")]
sys.modules[package.__name__] = package
spec = importlib.util.spec_from_file_location("store_test_package.store", Path(__file__).parents[1] / "src/lic_dsf/store.py")
store = importlib.util.module_from_spec(spec)
spec.loader.exec_module(store)


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)
        self.s = store.ScenarioStore(self.path / "workspace")
        self.sha = "a" * 64
        self.s.register_workbook(self.sha, "Local source")
        self.definition = {"delta_paths": {"11": [0.0, 1.0]}, "terms": None}
        self.case = self.s.save_scenario(self.sha, "Internal draft name", self.definition, share_label="Growth scenario")
        self.identity = {"engine": "test-engine", "version": "1"}

    def tearDown(self):
        self.temp.cleanup()

    def result(self, **changes):
        return dict({"workbook_sha256": self.sha, "scenario": self.definition, "engine_identity": self.identity,
                     "scenario_hash": store.digest(self.definition),
                     "contract_version": "test-1", "points": [{"year": 2030, "scenario": 2.25}],
                     "evidence": {"live_excel": "pending"}}, **changes)

    def current(self, sid=None, identity=None):
        return self.s.current_run(sid or self.case["id"], engine_identity=identity or self.identity, contract_version="test-1")

    def test_roundtrip_preserves_exact_record_and_private_reasoning(self):
        result = self.result()
        self.s.record_run(self.case["id"], result, expected_revision=1)
        self.s.add_reasoning(self.case["id"], "First interpretation")
        self.s.add_reasoning(self.case["id"], "Revised interpretation")
        self.s = store.ScenarioStore(self.path / "workspace")
        self.assertEqual(self.current()["result"], result)
        self.assertEqual(len(self.s.reasoning_history(self.case["id"])), 2)
        self.assertNotIn("reasoning", self.current())
        self.assertNotIn("name", self.current())

    def test_late_calculation_cannot_attach_after_edit(self):
        edited = {"delta_paths": {"11": [0, 2]}, "terms": None}
        self.s.save_scenario(self.sha, "Edited", edited, scenario_id=self.case["id"], expected_revision=1)
        with self.assertRaises(store.StaleResult):
            self.s.record_run(self.case["id"], self.result(), expected_revision=1)

    def test_restore_inputs_still_needs_current_revision_result(self):
        self.s.record_run(self.case["id"], self.result(), expected_revision=1)
        self.s.save_scenario(self.sha, "Changed", {"delta_paths": {}, "terms": None}, scenario_id=self.case["id"], expected_revision=1)
        self.s.save_scenario(self.sha, "Restored", self.definition, scenario_id=self.case["id"], expected_revision=2)
        with self.assertRaises(store.StaleResult):
            self.current()
        self.s.record_run(self.case["id"], self.result(), expected_revision=3)
        self.assertEqual(self.current()["revision"], 3)

    def test_new_engine_invalidates_saved_result(self):
        self.s.record_run(self.case["id"], self.result(), expected_revision=1)
        with self.assertRaises(store.StaleResult):
            self.current(identity={"engine": "test-engine", "version": "2"})

    def test_wrong_workbook_and_wrong_definition_cannot_be_attached(self):
        for result in [self.result(workbook_sha256="b" * 64), self.result(scenario={})]:
            with self.assertRaises(store.StaleResult):
                self.s.record_run(self.case["id"], result, expected_revision=1)

    def test_cross_workbook_comparison_refused(self):
        other_sha = "b" * 64
        self.s.register_workbook(other_sha, "Different source")
        other = self.s.save_scenario(other_sha, "Other", self.definition)
        with self.assertRaisesRegex(ValueError, "same workbook"):
            self.s.comparison([self.case["id"], other["id"]], self.case["id"], engine_identity=self.identity, contract_version="test-1")

    def test_backup_is_reopenable_and_does_not_overwrite(self):
        self.s.record_run(self.case["id"], self.result(), expected_revision=1)
        backup = self.s.backup(self.path / "backup/scenarios.sqlite3")
        restored = store.ScenarioStore(backup.parent)
        self.assertEqual(restored.get_scenario(self.case["id"])["definition"], self.definition)
        with self.assertRaises(ValueError):
            self.s.backup(backup)

    def test_nonfinite_definition_is_rejected(self):
        with self.assertRaises(ValueError):
            self.s.save_scenario(self.sha, "Invalid", {"value": float("nan")})

    def test_overlapping_save_requires_reload(self):
        saved = self.s.save_scenario(self.sha, "First edit", self.definition, scenario_id=self.case["id"], expected_revision=1)
        self.assertEqual(saved["revision"], 2)
        with self.assertRaises(store.StaleResult):
            self.s.save_scenario(self.sha, "Second edit", self.definition, scenario_id=self.case["id"], expected_revision=1)

    def test_incorrect_declared_scenario_identity_is_rejected(self):
        with self.assertRaises(store.StaleResult):
            self.s.record_run(self.case["id"], self.result(scenario_hash="incorrect"), expected_revision=1)

    def test_label_only_revision_keeps_current_result(self):
        result = self.result()
        self.s.record_run(self.case["id"], result, expected_revision=1)
        saved = self.s.save_scenario(self.sha, "Renamed draft", self.definition, scenario_id=self.case["id"],
                                     expected_revision=1, share_label="Lower growth")
        self.assertEqual(saved["revision"], 2)
        current = self.current()
        self.assertEqual(current["result"], result)
        self.assertEqual(current["revision"], 2)
        self.assertEqual(current["share_label"], "Lower growth")

    def test_explanation_only_revision_keeps_current_result(self):
        self.s.record_run(self.case["id"], self.result(), expected_revision=1)
        self.s.save_scenario(self.sha, "Internal draft name", self.definition, scenario_id=self.case["id"],
                             expected_revision=1, share_label="Growth scenario", shared_rationale={"11": "Revenue effort."})
        current = self.current()
        self.assertEqual(current["revision"], 2)
        self.assertEqual(current["shared_rationale"], {"11": "Revenue effort."})
        self.assertEqual(current["result"], self.result())

    def test_numerical_change_after_label_revision_still_needs_calculation(self):
        self.s.record_run(self.case["id"], self.result(), expected_revision=1)
        self.s.save_scenario(self.sha, "Renamed", self.definition, scenario_id=self.case["id"], expected_revision=1, share_label="Case")
        edited = {"delta_paths": {"11": [0, 2]}, "terms": None}
        self.s.save_scenario(self.sha, "Edited", edited, scenario_id=self.case["id"], expected_revision=2, share_label="Case")
        with self.assertRaises(store.StaleResult):
            self.current()
        self.s.save_scenario(self.sha, "Restored", self.definition, scenario_id=self.case["id"], expected_revision=3, share_label="Case")
        with self.assertRaises(store.StaleResult):
            self.current()
        self.s.record_run(self.case["id"], self.result(), expected_revision=4)
        self.assertEqual(self.current()["revision"], 4)
        self.s.save_scenario(self.sha, "Restored and renamed", self.definition, scenario_id=self.case["id"], expected_revision=4, share_label="Case B")
        self.assertEqual(self.current()["revision"], 5)
        self.assertEqual(self.current()["share_label"], "Case B")

    def test_comparison_after_label_revision_reports_current_label_and_revision(self):
        self.s.record_run(self.case["id"], self.result(), expected_revision=1)
        self.s.save_scenario(self.sha, "Renamed", self.definition, scenario_id=self.case["id"], expected_revision=1, share_label="Control")
        comparison = self.s.comparison([self.case["id"]], self.case["id"], engine_identity=self.identity, contract_version="test-1")
        run = comparison["runs"][0]
        self.assertEqual((run["revision"], run["share_label"]), (2, "Control"))
        self.assertEqual(run["result"], self.result())



if __name__ == "__main__":
    unittest.main()
