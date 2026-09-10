from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from unittest import mock

from test_store import store


class ContextStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)
        self.s = store.ScenarioStore(self.path)
        self.sha = "a" * 64
        self.s.register_workbook(self.sha, "Internal source name.xlsx")
        self.definition = {"delta_paths": {"11": [0, 1]}, "terms": None}
        self.case = self.s.save_scenario(self.sha, "Internal case name", self.definition, share_label="Growth")
        self.identity = {"engine": "neutral-engine", "version": "1"}
        self.result = {"workbook_sha256": self.sha, "scenario": self.definition,
                       "scenario_hash": store.digest(self.definition), "engine_identity": self.identity,
                       "contract_version": "test-1", "points": [{"year": 2030, "scenario": 2.25}],
                       "evidence": {"live_excel": "pending"}}
        self.s.record_run(self.case["id"], self.result, expected_revision=1)
        self.s.add_reasoning(self.case["id"], "Private reasoning sentinel")

    def tearDown(self):
        self.temp.cleanup()

    def compare(self, **kwargs):
        return self.s.comparison([self.case["id"]], self.case["id"],
                                 engine_identity=self.identity, contract_version="test-1", **kwargs)

    def numerical_rows(self):
        with sqlite3.connect(self.s.database) as db:
            return {table: list(db.execute(f"SELECT * FROM {table} ORDER BY rowid"))
                    for table in ("workbooks", "scenarios", "revisions", "runs", "reasoning")}

    def make_version1(self):
        # The base tables remain exactly the original version1 layout.
        with sqlite3.connect(self.s.database) as db:
            db.execute("DROP TABLE chart_context")
            db.execute("UPDATE metadata SET value='1' WHERE key='schema_version'")

    def test_migration_preserves_every_existing_record(self):
        before = self.numerical_rows()
        self.make_version1()
        self.s = store.ScenarioStore(self.path)
        self.assertEqual(self.numerical_rows(), before)
        self.assertEqual(self.s.get_chart_context(self.sha),
                         {"workbook_sha256": self.sha, "label": None, "revision": 0})
        with sqlite3.connect(self.s.database) as db:
            self.assertEqual(db.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0], "2")

    def test_unknown_future_and_malformed_schemas_preserve_bytes(self):
        for name, statements in (
            ("future", ["CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL)",
                        "INSERT INTO metadata VALUES('schema_version','99')"]),
            ("incomplete", ["CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL)",
                            "INSERT INTO metadata VALUES('schema_version','1')"]),
            ("unversioned", ["CREATE TABLE private_notes(text TEXT)"]),
        ):
            directory = self.path / name
            directory.mkdir()
            database = directory / "scenarios.sqlite3"
            with sqlite3.connect(database) as db:
                for statement in statements:
                    db.execute(statement)
            database.chmod(0o640)
            before, mode = database.read_bytes(), database.stat().st_mode
            with self.subTest(name=name), self.assertRaises(ValueError):
                store.ScenarioStore(directory)
            self.assertEqual(database.read_bytes(), before)
            self.assertEqual(database.stat().st_mode, mode)
        with sqlite3.connect(self.s.database) as db:
            db.execute("UPDATE metadata SET value='1' WHERE key='schema_version'")
        before = self.s.database.read_bytes()
        with self.assertRaises(ValueError):
            store.ScenarioStore(self.path)
        self.assertEqual(self.s.database.read_bytes(), before)

    def test_failure_after_ddl_rolls_back_and_retry_works(self):
        self.make_version1()
        before = self.s.database.read_bytes()
        original_connect = sqlite3.connect

        class FailingConnection(sqlite3.Connection):
            def execute(self, sql, *args):
                if sql.startswith("INSERT OR REPLACE INTO metadata"):
                    raise sqlite3.OperationalError("neutral injected migration fault")
                return super().execute(sql, *args)

        def connect(*args, **kwargs):
            return original_connect(*args, factory=FailingConnection, **kwargs)

        with mock.patch.object(store.sqlite3, "connect", side_effect=connect):
            with self.assertRaises(ValueError):
                store.ScenarioStore(self.path)
        self.assertEqual(self.s.database.read_bytes(), before)
        self.assertEqual(store.ScenarioStore(self.path).get_chart_context(self.sha)["revision"], 0)

    def test_generated_columns_and_missing_constraints_refuse_without_mutation(self):
        for case in ("generated_column", "missing_check", "weakened_check"):
            directory = self.path / case
            candidate = store.ScenarioStore(directory)
            with sqlite3.connect(candidate.database) as db:
                if case == "generated_column":
                    db.execute("DROP TABLE chart_context")
                    db.execute("UPDATE metadata SET value='1' WHERE key='schema_version'")
                    db.execute("ALTER TABLE workbooks ADD COLUMN unexpected TEXT GENERATED ALWAYS AS ('unexpected') VIRTUAL")
                else:
                    db.execute("DROP TABLE chart_context")
                    changed = (store._CONTEXT_SCHEMA.replace(" CHECK (revision >= 1)", "") if case == "missing_check"
                               else store._CONTEXT_SCHEMA.replace("revision >= 1", "revision >= 0"))
                    db.execute(changed)
            candidate.database.chmod(0o640)
            before, mode = candidate.database.read_bytes(), candidate.database.stat().st_mode
            with self.subTest(case=case), self.assertRaises(ValueError):
                store.ScenarioStore(directory)
            self.assertEqual(candidate.database.read_bytes(), before)
            self.assertEqual(candidate.database.stat().st_mode, mode)

    def test_original_if_not_exists_ddl_and_whitespace_remain_compatible(self):
        directory = self.path / "original_layout"
        directory.mkdir()
        database = directory / "scenarios.sqlite3"
        with sqlite3.connect(database) as db:
            for sql in store._BASE_SCHEMA:
                db.execute(sql.replace("CREATE TABLE ", "CREATE TABLE IF NOT EXISTS ")
                           .replace("\n        ", "\n                    "))
            db.execute("INSERT INTO metadata VALUES ('schema_version','1')")
            db.execute("INSERT INTO workbooks VALUES (?,?,?)", (self.sha, "Original internal label", "2030-01-01"))
        restored = store.ScenarioStore(directory)
        self.assertEqual(restored.get_chart_context(self.sha)["revision"], 0)
        with sqlite3.connect(database) as db:
            self.assertEqual(db.execute("SELECT label,created FROM workbooks").fetchone(),
                             ("Original internal label", "2030-01-01"))

    def test_concurrent_initializers_recheck_under_lock(self):
        self.make_version1()
        before = self.numerical_rows()
        barrier = threading.Barrier(2)

        def initialize(_):
            barrier.wait(timeout=5)
            return store.ScenarioStore(self.path).get_chart_context(self.sha)

        with ThreadPoolExecutor(max_workers=2) as pool:
            contexts = list(pool.map(initialize, range(2)))
        self.assertEqual(contexts[0], contexts[1])
        self.assertEqual(self.numerical_rows(), before)

    def test_context_changes_do_not_rewrite_calculations_or_reasoning(self):
        before = self.numerical_rows()
        old = self.compare()
        self.assertIsNone(old["chart_context"]["label"])
        saved = self.s.save_chart_context(self.sha, "Budget: FY2030/31", expected_revision=0)
        current = self.compare(workbook_sha=self.sha, expected_chart_context_revision=1)
        self.assertEqual(current["runs"], old["runs"])
        self.assertEqual(current["chart_context"], saved)
        self.assertEqual(self.numerical_rows(), before)
        self.assertNotIn("Internal source", store.canonical(current))
        self.assertNotIn("Private reasoning", store.canonical(current))
        self.assertNotIn("Internal case", store.canonical(current))

    def test_clear_and_seed_preserve_deliberate_analyst_choices(self):
        first = self.s.seed_chart_context(self.sha, "Illustrative analysis")
        self.assertEqual(first["revision"], 1)
        self.assertEqual(self.s.seed_chart_context(self.sha, "Different seed"), first)
        edited = self.s.save_chart_context(self.sha, "Analyst label", expected_revision=1)
        self.assertEqual(self.s.seed_chart_context(self.sha, "Different seed"), edited)
        cleared = self.s.save_chart_context(self.sha, "  ", expected_revision=2)
        self.assertEqual(cleared["revision"], 3)
        self.assertIsNone(cleared["label"])
        self.assertEqual(store.ScenarioStore(self.path).seed_chart_context(self.sha, "Different seed"), cleared)

    def test_first_explicit_clear_creates_row_and_noop_requires_current_revision(self):
        clear = self.s.save_chart_context(self.sha, None, expected_revision=0)
        self.assertEqual(clear["revision"], 1)
        self.assertEqual(self.s.seed_chart_context(self.sha, "Seed"), clear)
        self.assertEqual(self.s.save_chart_context(self.sha, " ", expected_revision=1), clear)
        with self.assertRaises(store.StaleResult):
            self.s.save_chart_context(self.sha, None, expected_revision=0)

    def test_concurrent_context_edit_has_one_winner(self):
        self.s.seed_chart_context(self.sha, "Initial")
        barrier = threading.Barrier(2)

        def save(label):
            barrier.wait(timeout=5)
            try:
                return self.s.save_chart_context(self.sha, label, expected_revision=1)
            except store.StaleResult:
                return "conflict"

        with ThreadPoolExecutor(max_workers=2) as pool:
            answers = list(pool.map(save, ("First writer", "Second writer")))
        self.assertEqual(answers.count("conflict"), 1)
        self.assertEqual(self.s.get_chart_context(self.sha)["revision"], 2)

    def test_source_and_context_revision_required_together(self):
        for request in ({"workbook_sha": self.sha}, {"expected_chart_context_revision": 0},
                        {"workbook_sha": self.sha, "expected_chart_context_revision": True},
                        {"workbook_sha": "b" * 64, "expected_chart_context_revision": 0}):
            with self.subTest(request=request), self.assertRaises(ValueError):
                self.compare(**request)
        self.s.seed_chart_context(self.sha, "New label")
        with self.assertRaises(store.StaleResult):
            self.compare(workbook_sha=self.sha, expected_chart_context_revision=0)

    def test_comparison_context_is_in_same_snapshot_as_scenarios(self):
        with sqlite3.connect(self.s.database) as db:
            db.execute("PRAGMA journal_mode=WAL")
        original = self.s._chart_context
        changed = False

        def context_after_concurrent_commit(db, sha):
            nonlocal changed
            if not changed:
                changed = True
                writer = store.ScenarioStore(self.path)
                writer.seed_chart_context(self.sha, "Committed during comparison")
            return original(db, sha)

        with mock.patch.object(self.s, "_chart_context", side_effect=context_after_concurrent_commit):
            comparison = self.compare(workbook_sha=self.sha, expected_chart_context_revision=0)
        self.assertIsNone(comparison["chart_context"]["label"])
        self.assertEqual(comparison["chart_context"]["revision"], 0)
        self.assertEqual(self.s.get_chart_context(self.sha)["revision"], 1)

    def test_corrupt_label_rejected_and_prefix_collisions_stay_separate(self):
        other_sha = "a" * 12 + "b" * 52
        self.s.register_workbook(other_sha, "Internal source name.xlsx")
        self.s.seed_chart_context(self.sha, "First context")
        self.s.seed_chart_context(other_sha, "Second context")
        self.assertNotEqual(self.s.get_chart_context(self.sha)["label"], self.s.get_chart_context(other_sha)["label"])
        with sqlite3.connect(self.s.database) as db:
            db.execute("UPDATE chart_context SET label=' Noncanonical ' WHERE workbook_sha=?", (self.sha,))
        for action in (lambda: self.s.get_chart_context(self.sha), self.compare,
                       lambda: self.s.seed_chart_context(self.sha, "Replacement")):
            with self.assertRaises(ValueError):
                action()

    def test_unknown_source_and_invalid_write_rejected_without_changes(self):
        before = self.s.database.read_bytes()
        actions = (lambda: self.s.get_chart_context("b" * 64),
                   lambda: self.s.save_chart_context("b" * 64, "Label", expected_revision=0),
                   lambda: self.s.save_chart_context(self.sha, "C:private", expected_revision=0),
                   lambda: self.s.save_chart_context(self.sha, "Label", expected_revision=True),
                   lambda: self.s.seed_chart_context(self.sha, None))
        for action in actions:
            with self.assertRaises(ValueError):
                action()
        self.assertEqual(self.s.database.read_bytes(), before)

    def test_context_and_unchanged_runs_survive_existing_backup_route(self):
        context = self.s.save_chart_context(self.sha, "Budget: FY2030/31", expected_revision=0)
        before = self.compare()
        backup = self.s.backup(self.path / "restored/scenarios.sqlite3")
        restored = store.ScenarioStore(backup.parent)
        self.assertEqual(restored.get_chart_context(self.sha), context)
        after = restored.comparison([self.case["id"]], self.case["id"],
                                    engine_identity=self.identity, contract_version="test-1",
                                    workbook_sha=self.sha, expected_chart_context_revision=1)
        self.assertEqual(before, after)
        self.assertEqual(self.s.reasoning_history(self.case["id"]), restored.reasoning_history(self.case["id"]))


if __name__ == "__main__":
    unittest.main()
