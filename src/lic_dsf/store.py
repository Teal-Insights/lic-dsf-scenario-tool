"""Local scenario journals. Calculation records are stored without alteration."""
from __future__ import annotations

from contextlib import closing, contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile
import unicodedata
import uuid

from .chart_context import normalize_context_label, validate_chart_context
from .rationale import normalize_rationale


_BASE_SCHEMA = (
    "CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)",
    "CREATE TABLE workbooks (sha TEXT PRIMARY KEY, label TEXT NOT NULL, created TEXT NOT NULL)",
    """CREATE TABLE scenarios (
        id TEXT PRIMARY KEY, workbook_sha TEXT NOT NULL REFERENCES workbooks(sha), current_revision INTEGER NOT NULL
    )""",
    """CREATE TABLE revisions (
        scenario_id TEXT NOT NULL REFERENCES scenarios(id), revision INTEGER NOT NULL,
        name TEXT NOT NULL, share_label TEXT NOT NULL, definition TEXT NOT NULL,
        definition_hash TEXT NOT NULL, created TEXT NOT NULL,
        PRIMARY KEY (scenario_id, revision)
    )""",
    """CREATE TABLE runs (
        id TEXT PRIMARY KEY, scenario_id TEXT NOT NULL, revision INTEGER NOT NULL,
        definition_hash TEXT NOT NULL, engine_identity TEXT NOT NULL, contract_version TEXT NOT NULL,
        result TEXT NOT NULL, result_hash TEXT NOT NULL, created TEXT NOT NULL,
        FOREIGN KEY (scenario_id, revision) REFERENCES revisions(scenario_id, revision)
    )""",
    """CREATE TABLE reasoning (
        id TEXT PRIMARY KEY, scenario_id TEXT NOT NULL REFERENCES scenarios(id),
        revision INTEGER NOT NULL, text TEXT NOT NULL, created TEXT NOT NULL
    )""",
)
_CONTEXT_SCHEMA = """CREATE TABLE chart_context (
    workbook_sha TEXT PRIMARY KEY REFERENCES workbooks(sha), label TEXT,
    revision INTEGER NOT NULL CHECK (revision >= 1), updated TEXT NOT NULL
)"""
_RATIONALE_SCHEMA = """CREATE TABLE shared_rationale (
    scenario_id TEXT NOT NULL, revision INTEGER NOT NULL,
    notes TEXT NOT NULL, notes_hash TEXT NOT NULL,
    PRIMARY KEY (scenario_id, revision),
    FOREIGN KEY (scenario_id, revision) REFERENCES revisions(scenario_id, revision)
)"""
_BASE_TABLES = {"metadata", "workbooks", "scenarios", "revisions", "runs", "reasoning"}
_SCHEMA_ERROR = "This saved workspace requires a different application version or a valid workspace backup."
_CONTEXT_CONFLICT = "The chart context changed. Reload it before saving or exporting."
_LABEL_CONFLICT = "A case was changed in another tab. Nothing was applied; choose Discard edits and keep saved text to reload, then apply again."
_SHARE_LABEL_ERROR = "Use a legend label of 1 to 40 characters without paths, links or control characters."
_SHARE_LABEL_PATTERN = re.compile(r"[\x00-\x1f/\\]|https?:|file:|[A-Za-z]:")


def normalize_share_label(value):
    """Return a legend label the chart renderer accepts, or refuse it."""
    if not isinstance(value, str):
        raise ValueError(_SHARE_LABEL_ERROR)
    label = unicodedata.normalize("NFC", value).strip()
    if not 1 <= len(label) <= 40 or _SHARE_LABEL_PATTERN.search(label):
        raise ValueError(_SHARE_LABEL_ERROR)
    if label.casefold() == "reference baseline":
        raise ValueError("“Reference baseline” names the workbook baseline on every chart. Choose a different legend label.")
    return label


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


class StaleResult(ValueError):
    """The scenario has no result for the requested definition and runtime."""


class ScenarioStore:
    def __init__(self, data_directory):
        self.directory = Path(data_directory).expanduser().resolve()
        if self.directory == Path(__file__).resolve().parent or Path(__file__).resolve().parent in self.directory.parents:
            raise ValueError("Choose a data directory outside the installed package.")
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.database = self.directory / "scenarios.sqlite3"
        try:
            # An incompatible existing file must not be changed even by initialization.
            if self.database.exists():
                with closing(sqlite3.connect(self.database.as_uri() + "?mode=ro", uri=True)) as inspection:
                    self._schema_version(inspection)
            with self._connection() as db:
                db.execute("BEGIN IMMEDIATE")
                # Another initializer may have completed while this connection waited.
                version = self._schema_version(db)
                if version == 0:
                    for statement in _BASE_SCHEMA:
                        db.execute(statement)
                if version < 2:
                    db.execute(_CONTEXT_SCHEMA)
                if version < 3:
                    db.execute(_RATIONALE_SCHEMA)
                    db.execute("INSERT INTO shared_rationale SELECT scenario_id,revision,?,? FROM revisions",
                               (canonical({}), digest({})))
                    db.execute("INSERT OR REPLACE INTO metadata VALUES ('schema_version','3')")
        except sqlite3.DatabaseError as exc:
            raise ValueError(_SCHEMA_ERROR) from exc
        self.database.chmod(0o600)

    @staticmethod
    def _schema_version(db):
        objects = {(row[0], row[1]) for row in db.execute(
            "SELECT type,name FROM sqlite_master WHERE substr(name,1,7) != 'sqlite_'"
        )}
        if not objects:
            return 0
        if ("table", "metadata") not in objects:
            raise ValueError(_SCHEMA_ERROR)
        versions = list(db.execute("SELECT value FROM metadata WHERE key='schema_version'"))
        if len(versions) != 1 or versions[0][0] not in ("1", "2", "3"):
            raise ValueError(_SCHEMA_ERROR)
        version = int(versions[0][0])
        tables = _BASE_TABLES | ({"chart_context"} if version >= 2 else set()) | ({"shared_rationale"} if version >= 3 else set())
        if objects != {("table", name) for name in tables}:
            raise ValueError(_SCHEMA_ERROR)
        # Compare the known structural layout in memory; no DDL touches the caller's
        # file until its version and base tables have passed inspection.
        with closing(sqlite3.connect(":memory:")) as reference:
            for statement in _BASE_SCHEMA + ((_CONTEXT_SCHEMA,) if version >= 2 else ()) + ((_RATIONALE_SCHEMA,) if version >= 3 else ()):
                reference.execute(statement)
            for name in tables:
                for pragma in ("table_xinfo", "foreign_key_list"):
                    query = f"PRAGMA {pragma}({name})"
                    if [tuple(row) for row in db.execute(query)] != list(reference.execute(query)):
                        raise ValueError(_SCHEMA_ERROR)
                query = "SELECT sql FROM sqlite_master WHERE type='table' AND name=?"
                actual = db.execute(query, (name,)).fetchone()[0]
                expected = reference.execute(query, (name,)).fetchone()[0]
                # SQLite's column pragmas omit CHECK constraints and other table
                # semantics. Our known DDL uses no quoted literals/identifiers;
                # tolerate only whitespace/case differences from its original form.
                if "".join(actual.split()).casefold() != "".join(expected.split()).casefold():
                    raise ValueError(_SCHEMA_ERROR)
        return version

    @contextmanager
    def _connection(self):
        db = sqlite3.connect(self.database, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def register_workbook(self, sha, label):
        if not re.fullmatch(r"[0-9a-f]{64}", sha):
            raise ValueError("A valid workbook SHA-256 is required.")
        if not isinstance(label, str) or not label.strip() or len(label) > 300:
            raise ValueError("A short workbook label is required.")
        with self._connection() as db:
            db.execute("INSERT OR IGNORE INTO workbooks VALUES (?,?,?)", (sha, label.strip(), now()))

    @staticmethod
    def _chart_context(db, workbook_sha):
        empty = validate_chart_context(
            {"workbook_sha256": workbook_sha, "label": None, "revision": 0}, workbook_sha
        )
        if db.execute("SELECT 1 FROM workbooks WHERE sha=?", (workbook_sha,)).fetchone() is None:
            raise ValueError("Register the workbook before editing its chart context.")
        row = db.execute("SELECT label,revision FROM chart_context WHERE workbook_sha=?", (workbook_sha,)).fetchone()
        if row is None:
            return empty
        if type(row["revision"]) is not int or row["revision"] < 1:
            raise ValueError("The saved chart context failed its integrity check.")
        return validate_chart_context(
            {"workbook_sha256": workbook_sha, "label": row["label"], "revision": row["revision"]}, workbook_sha
        )

    def get_chart_context(self, workbook_sha):
        with self._connection() as db:
            db.execute("BEGIN")
            return self._chart_context(db, workbook_sha)

    def save_chart_context(self, workbook_sha, label, *, expected_revision):
        label = normalize_context_label(label)
        if type(expected_revision) is not int or expected_revision < 0:
            raise ValueError("A valid chart context revision is required.")
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            current = self._chart_context(db, workbook_sha)
            if current["revision"] != expected_revision:
                raise StaleResult(_CONTEXT_CONFLICT)
            if current["revision"] > 0 and current["label"] == label:
                return current
            revision = current["revision"] + 1
            db.execute("""INSERT INTO chart_context VALUES (?,?,?,?)
                ON CONFLICT(workbook_sha) DO UPDATE SET label=excluded.label,
                revision=excluded.revision,updated=excluded.updated""", (workbook_sha, label, revision, now()))
            return self._chart_context(db, workbook_sha)

    def seed_chart_context(self, workbook_sha, label):
        label = normalize_context_label(label)
        if label is None:
            raise ValueError("An explicit nonblank chart label is required for a seed.")
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            current = self._chart_context(db, workbook_sha)
            if current["revision"] > 0:
                return current
            db.execute("INSERT INTO chart_context VALUES (?,?,1,?)", (workbook_sha, label, now()))
            return self._chart_context(db, workbook_sha)

    def save_chart_text(self, workbook_sha, labels, heading=None, *, expected_context_revision):
        """Apply legend-label revisions and an optional heading together or not at all.

        Every value is validated before any write, every expected revision is
        compared inside one BEGIN IMMEDIATE transaction, and any refusal rolls
        the whole operation back, so partially applied chart text cannot exist.
        `labels` holds {scenario_id, expected_revision, share_label} items;
        `heading` is None (unchanged) or {"label": text or None}. A label-only
        revision keeps the case's name, inputs, explanations and calculation.
        """
        if not isinstance(workbook_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", workbook_sha):
            raise ValueError("A valid workbook SHA-256 is required.")
        if type(expected_context_revision) is not int or expected_context_revision < 0:
            raise ValueError("A valid chart context revision is required.")
        if not isinstance(labels, list) or len(labels) > 50:
            raise ValueError("Provide the legend labels to apply as a list.")
        updates = {}
        for item in labels:
            if (not isinstance(item, dict) or set(item) != {"scenario_id", "expected_revision", "share_label"}
                    or not isinstance(item["scenario_id"], str) or type(item["expected_revision"]) is not int
                    or item["scenario_id"] in updates):
                raise ValueError("Provide each legend label with its scenario and expected revision once.")
            updates[item["scenario_id"]] = (item["expected_revision"], normalize_share_label(item["share_label"]))
        heading_label = None
        if heading is not None:
            if not isinstance(heading, dict) or set(heading) != {"label"}:
                raise ValueError("Provide the heading as a label.")
            heading_label = normalize_context_label(heading["label"])
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            context = self._chart_context(db, workbook_sha)
            if context["revision"] != expected_context_revision:
                raise StaleResult(_CONTEXT_CONFLICT)
            rows = {r["id"]: r for r in db.execute("""SELECT s.id, r.revision, r.name, r.share_label, r.definition, r.definition_hash
                FROM scenarios s JOIN revisions r ON s.id=r.scenario_id AND s.current_revision=r.revision
                WHERE s.workbook_sha=?""", (workbook_sha,))}
            for sid, (expected, label) in updates.items():
                if sid not in rows:
                    raise ValueError("The scenario does not belong to this workbook.")
                if rows[sid]["revision"] != expected:
                    raise StaleResult(_LABEL_CONFLICT)
            final = {sid: (updates[sid][1] if sid in updates else row["share_label"]) for sid, row in rows.items()}
            for sid in updates:
                key = unicodedata.normalize("NFC", final[sid]).strip().casefold()
                for other, label in final.items():
                    if other != sid and unicodedata.normalize("NFC", label).strip().casefold() == key:
                        raise ValueError("Two cases would share the legend label “" + final[sid] + "”. Choose distinct labels so both can appear on one chart.")
            stamp = now()
            for sid, (expected, label) in updates.items():
                row = rows[sid]
                if label == row["share_label"]:
                    continue
                note = db.execute("SELECT notes,notes_hash FROM shared_rationale WHERE scenario_id=? AND revision=?", (sid, row["revision"])).fetchone()
                if note is None:
                    raise StaleResult("The saved shared explanations failed their integrity check.")
                revision = row["revision"] + 1
                db.execute("UPDATE scenarios SET current_revision=? WHERE id=?", (revision, sid))
                db.execute("INSERT INTO revisions VALUES (?,?,?,?,?,?,?)",
                           (sid, revision, row["name"], label, row["definition"], row["definition_hash"], stamp))
                db.execute("INSERT INTO shared_rationale VALUES (?,?,?,?)", (sid, revision, note["notes"], note["notes_hash"]))
            if heading is not None and not (context["revision"] > 0 and context["label"] == heading_label):
                db.execute("""INSERT INTO chart_context VALUES (?,?,?,?)
                    ON CONFLICT(workbook_sha) DO UPDATE SET label=excluded.label,
                    revision=excluded.revision,updated=excluded.updated""", (workbook_sha, heading_label, context["revision"] + 1, stamp))
            return {"chart_context": self._chart_context(db, workbook_sha),
                    "scenarios": [self._scenario(db, sid) for sid in updates]}

    def save_scenario(self, workbook_sha, name, definition, *, scenario_id=None, expected_revision=None, share_label="Scenario", shared_rationale=None):
        if not isinstance(name, str) or not name.strip() or len(name) > 160:
            raise ValueError("Name the scenario using at most 160 characters.")
        if not isinstance(share_label, str) or not share_label.strip() or len(share_label) > 100:
            raise ValueError("A short label for shared charts is required.")
        notes = None if shared_rationale is None else normalize_rationale(shared_rationale)
        encoded = canonical(definition)
        identity = digest(definition)
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM workbooks WHERE sha=?", (workbook_sha,)).fetchone() is None:
                raise ValueError("Register the workbook before saving its scenarios.")
            if notes is None:
                notes = {} if scenario_id is None else self._scenario(db, scenario_id)["shared_rationale"]
            if scenario_id is None:
                scenario_id, revision = uuid.uuid4().hex, 1
                db.execute("INSERT INTO scenarios VALUES (?,?,?)", (scenario_id, workbook_sha, revision))
            else:
                row = db.execute("SELECT * FROM scenarios WHERE id=?", (scenario_id,)).fetchone()
                if row is None or row["workbook_sha"] != workbook_sha:
                    raise ValueError("The scenario does not belong to this workbook.")
                if expected_revision is None or row["current_revision"] != expected_revision:
                    raise StaleResult("The scenario changed. Reload it before saving your edit.")
                revision = row["current_revision"] + 1
                db.execute("UPDATE scenarios SET current_revision=? WHERE id=?", (revision, scenario_id))
            db.execute("INSERT INTO revisions VALUES (?,?,?,?,?,?,?)",
                       (scenario_id, revision, name.strip(), share_label.strip(), encoded, identity, now()))
            db.execute("INSERT INTO shared_rationale VALUES (?,?,?,?)",
                       (scenario_id, revision, canonical(notes), digest(notes)))
            snapshot = self._scenario(db, scenario_id)
        return snapshot

    def get_scenario(self, scenario_id):
        with self._connection() as db:
            return self._scenario(db, scenario_id)

    def _scenario(self, db, scenario_id):
        row = db.execute("""SELECT s.id,s.workbook_sha,r.* FROM scenarios s JOIN revisions r
            ON s.id=r.scenario_id AND s.current_revision=r.revision WHERE s.id=?""", (scenario_id,)).fetchone()
        if row is None:
            raise ValueError("Scenario not found.")
        result = dict(row)
        result["definition"] = json.loads(result["definition"])
        if digest(result["definition"]) != result["definition_hash"]:
            raise StaleResult("The saved scenario failed its integrity check.")
        note = db.execute("SELECT notes,notes_hash FROM shared_rationale WHERE scenario_id=? AND revision=?",
                          (scenario_id, result['revision'])).fetchone()
        if note is None:
            raise StaleResult("The saved shared explanations failed their integrity check.")
        notes = json.loads(note['notes'])
        if digest(notes) != note['notes_hash'] or normalize_rationale(notes) != notes:
            raise StaleResult("The saved shared explanations failed their integrity check.")
        result['shared_rationale'] = notes
        return result

    def list_scenarios(self, workbook_sha):
        with self._connection() as db:
            ids = [r[0] for r in db.execute("SELECT id FROM scenarios WHERE workbook_sha=? ORDER BY rowid", (workbook_sha,))]
        return [self.get_scenario(sid) for sid in ids]

    def add_reasoning(self, scenario_id, text):
        if not isinstance(text, str) or len(text) > 20000:
            raise ValueError("Reasoning must be text of at most 20,000 characters.")
        scenario = self.get_scenario(scenario_id)
        note_id = uuid.uuid4().hex
        with self._connection() as db:
            db.execute("INSERT INTO reasoning VALUES (?,?,?,?,?)",
                       (note_id, scenario_id, scenario["revision"], text, now()))
        return note_id

    def reasoning_history(self, scenario_id):
        with self._connection() as db:
            return [dict(r) for r in db.execute("SELECT * FROM reasoning WHERE scenario_id=? ORDER BY rowid", (scenario_id,))]

    def record_run(self, scenario_id, result, *, expected_revision):
        # A calculation finishing after an edit cannot attach itself to the new revision.
        encoded = canonical(result)
        result_hash = digest(result)
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("""SELECT s.workbook_sha,s.current_revision,r.definition,r.definition_hash
                FROM scenarios s JOIN revisions r ON s.id=r.scenario_id AND s.current_revision=r.revision
                WHERE s.id=?""", (scenario_id,)).fetchone()
            if row is None or row["current_revision"] != expected_revision:
                raise StaleResult("The scenario changed while this calculation was running.")
            if row["workbook_sha"] != result.get("workbook_sha256") or canonical(result.get("scenario")) != row["definition"]:
                raise StaleResult("The calculation does not match the saved workbook and inputs.")
            if digest(json.loads(row["definition"])) != row["definition_hash"]:
                raise StaleResult("The saved scenario failed its integrity check.")
            if result.get("scenario_hash") != digest(result["scenario"]):
                raise StaleResult("The calculation's input identity failed its integrity check.")
            if not result.get("engine_identity") or not result.get("contract_version"):
                raise ValueError("Calculation runtime and contract identities are required.")
            run_id = uuid.uuid4().hex
            db.execute("INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?)", (
                run_id, scenario_id, expected_revision, row["definition_hash"], canonical(result["engine_identity"]),
                str(result["contract_version"]), encoded, result_hash, now()))
        return run_id

    def current_run(self, scenario_id, *, engine_identity, contract_version):
        with self._connection() as db:
            db.execute("BEGIN")
            return self._current_run(db, scenario_id, engine_identity=engine_identity, contract_version=contract_version)

    @staticmethod
    def _numerical_base_revision(db, scenario_id, revision, definition_hash):
        """Earliest revision from which every later revision kept this exact definition.

        Name, share-label and shared-explanation edits create revisions without
        changing the numerical definition; their calculation stays current. Any
        intervening numerical change breaks the chain, so a restored definition
        still needs its own calculation.
        """
        base = revision
        for row in db.execute("SELECT revision,definition_hash FROM revisions WHERE scenario_id=? AND revision<=? ORDER BY revision DESC",
                              (scenario_id, revision)):
            if row["definition_hash"] != definition_hash or row["revision"] != base:
                break
            base = row["revision"] - 1
        return base + 1

    def _current_run(self, db, scenario_id, *, engine_identity, contract_version):
        scenario = self._scenario(db, scenario_id)
        base = self._numerical_base_revision(db, scenario_id, scenario["revision"], scenario["definition_hash"])
        row = db.execute("""SELECT * FROM runs WHERE scenario_id=? AND revision BETWEEN ? AND ? AND definition_hash=?
            AND engine_identity=? AND contract_version=? ORDER BY revision DESC, rowid DESC LIMIT 1""",
            (scenario_id, base, scenario["revision"], scenario["definition_hash"], canonical(engine_identity), str(contract_version))).fetchone()
        if row is None:
            raise StaleResult("Calculate this saved scenario with the current engine before viewing or exporting its results.")
        result = json.loads(row["result"])
        if digest(result) != row["result_hash"]:
            raise StaleResult("The saved result failed its integrity check.")
        if (result.get("workbook_sha256") != scenario["workbook_sha"]
                or canonical(result.get("scenario")) != canonical(scenario["definition"])
                or result.get("scenario_hash") != scenario["definition_hash"]
                or canonical(result.get("engine_identity")) != canonical(engine_identity)
                or str(result.get("contract_version")) != str(contract_version)):
            raise StaleResult("The saved result's identities do not match this scenario and runtime.")
        return {"id": row["id"], "result_hash": row["result_hash"], "result": result,
                "scenario_id": scenario_id, "revision": scenario["revision"], "share_label": scenario["share_label"],
                "shared_rationale": scenario["shared_rationale"]}

    def comparison(self, scenario_ids, comparator_id, *, engine_identity, contract_version,
                   workbook_sha=None, expected_chart_context_revision=None):
        if (workbook_sha is None) != (expected_chart_context_revision is None):
            raise ValueError("Provide the workbook and chart context revision together.")
        if workbook_sha is not None:
            validate_chart_context({"workbook_sha256": workbook_sha, "label": None,
                                    "revision": expected_chart_context_revision}, workbook_sha)
        ids = list(dict.fromkeys(scenario_ids))
        if not ids or comparator_id not in ids:
            raise ValueError("Select scenarios and choose one as the comparator.")
        with self._connection() as db:
            db.execute("BEGIN")
            scenarios = [self._scenario(db, sid) for sid in ids]
            if len({s["workbook_sha"] for s in scenarios}) != 1:
                raise ValueError("Compare scenarios from the same workbook baseline.")
            actual_sha = scenarios[0]["workbook_sha"]
            if workbook_sha is not None and actual_sha != workbook_sha:
                raise ValueError("The comparison does not belong to the selected workbook.")
            context = self._chart_context(db, actual_sha)
            if expected_chart_context_revision is not None and context["revision"] != expected_chart_context_revision:
                raise StaleResult(_CONTEXT_CONFLICT)
            runs = [self._current_run(db, s["id"], engine_identity=engine_identity, contract_version=contract_version) for s in scenarios]
            # All selected definitions/results belong to one database snapshot.
            return {"workbook_sha256": actual_sha, "comparator_id": comparator_id, "runs": runs,
                    "chart_context": context}

    def backup(self, destination):
        target = Path(destination).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".scenario-backup-", dir=target.parent)
        os.close(fd)
        try:
            with self._connection() as source:
                backup_db = sqlite3.connect(temporary)
                try:
                    source.backup(backup_db)
                finally:
                    backup_db.close()
            # Atomic, exclusive publication of a completed backup, even if a competing
            # writer creates the destination after this operation began.
            try:
                os.link(temporary, target)
            except FileExistsError as exc:
                raise ValueError("Choose a new backup file so an earlier backup is preserved.") from exc
        finally:
            os.unlink(temporary)
        return target
