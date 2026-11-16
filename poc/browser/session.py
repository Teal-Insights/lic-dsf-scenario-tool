"""Application routes for the in-browser proof of concept.

The desktop application calculates in a subprocess. Pyodide has no
subprocess, so this module answers the same routes in the calling
interpreter and calls ``calculate`` directly. The browser worker loads
this file as source. It is not part of the installed package, so it does
not change the calculation identity.
"""
from __future__ import annotations

import json
import os
import shutil
import traceback
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

from lic_dsf.app import (
    MAX_UPLOAD,
    Workspace,
    checked_comparison_request,
    shareable,
)
from lic_dsf.official_example import OFFICIAL_EXAMPLE_SHA, verify_official_example
from lic_dsf.store import StaleResult, canonical

SESSION = None
# Pyodide's os module has no os.link. Resolve it when this file loads.
_HARDLINK = getattr(os, "link", None)
_PATH_CHMOD = Path.chmod


def link_or_copy(source, destination):
    """Hard-link a workbook copy, or copy the bytes when the filesystem cannot."""
    if _HARDLINK is None:
        if Path(destination).exists():
            raise FileExistsError(destination)
        shutil.copyfile(source, destination)
        return
    try:
        _HARDLINK(source, destination)
    except FileExistsError:
        raise
    except OSError:
        if Path(destination).exists():
            raise
        shutil.copyfile(source, destination)


def _tolerant_chmod(self, mode):
    try:
        _PATH_CHMOD(self, mode)
    except OSError:
        return None


def hardlinks_work(directory):
    if getattr(os, "link", None) is None:
        return False
    directory = Path(directory)
    source = directory / ".link-probe-source"
    destination = directory / ".link-probe-destination"
    source.write_bytes(b"x")
    try:
        os.link(source, destination)
    except (OSError, AttributeError):
        return False
    else:
        return True
    finally:
        source.unlink(missing_ok=True)
        destination.unlink(missing_ok=True)


def chmod_works(directory):
    probe = Path(directory) / ".chmod-probe"
    probe.write_bytes(b"x")
    try:
        probe.chmod(0o600)
    except (OSError, AttributeError):
        return False
    else:
        return True
    finally:
        probe.unlink(missing_ok=True)


def fsync_works(directory):
    if not hasattr(os, "fsync"):
        return False
    probe = Path(directory) / ".fsync-probe"
    probe.write_bytes(b"x")
    try:
        descriptor = os.open(probe, os.O_RDWR)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except (OSError, AttributeError):
        return False
    else:
        return True
    finally:
        probe.unlink(missing_ok=True)


def adapt_filesystem(directory):
    """Keep workbook intake working on the browser filesystem.

    IndexedDB-backed storage may reject hard links, permission changes or
    fsync. The desktop server keeps those calls. This process adapts only
    after a probe on its own data directory fails.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if not hardlinks_work(directory):
        os.link = link_or_copy
    if not chmod_works(directory):
        Path.chmod = _tolerant_chmod
    if not fsync_works(directory):
        os.fsync = lambda descriptor: None


def open_session(data_dir="/workspace"):
    global SESSION
    adapt_filesystem(data_dir)
    SESSION = BrowserSession(data_dir)
    return "ready"


def run_calculation(job_id):
    SESSION.run_calculation(job_id)


def dispatch_request():
    """Answer the request the worker wrote to /tmp. Used from JavaScript."""
    body_path = Path("/tmp/request-body")
    body = body_path.read_bytes() if body_path.is_file() else b""
    body_path.unlink(missing_ok=True)
    try:
        # The worker sets these names on the Python global scope for each request.
        status, content_type, payload, extra = SESSION.dispatch(
            globals()["req_method"], globals()["req_target"], body, json.loads(globals()["req_headers"]))
    except Exception:
        traceback.print_exc()
        status, content_type, payload = _pack(
            400, {"error": "The in-browser workspace could not answer. Saved work is retained."})
        extra = {"persist": False, "calculate": None}
    Path("/tmp/response-body").write_bytes(payload)
    return json.dumps({"status": status, "content_type": content_type, **extra})


def _pack(status, payload, content_type="application/json"):
    body = canonical(payload).encode() if content_type == "application/json" else payload
    return status, content_type, body


class BrowserSession:
    def __init__(self, data_dir):
        self.official_stage = Path("/tmp/official-example.xlsm")
        self.workspace = Workspace(SimpleNamespace(
            data_dir=str(data_dir),
            calculation_lock=None,
            calculation_timeout=240,
            example=None,
            example_sha256=None,
            example_label="Official IDA21 illustrative example",
            illustrative_example=False,
            edition_title="LIC-DSF Scenario Analysis Tool",
            edition_note=("In-browser proof of concept. Calculation runs in this tab with the "
                          "generated library. Saved work stays in this browser profile. "
                          "Fresh Excel verification remains pending."),
        ))

    def official_example_cached(self):
        cached = self.workspace.uploads / (OFFICIAL_EXAMPLE_SHA + ".xlsm")
        return cached.is_file() and not cached.is_symlink()

    def dispatch(self, method, target, body, headers):
        method = method.upper()
        header_map = {str(key).lower(): value for key, value in dict(headers).items()}
        try:
            if method == "GET":
                return (*self._get(target, header_map), {"persist": False, "calculate": None})
            if method == "POST":
                return self._post(target, body, header_map)
            return (*_pack(404, {"error": "Not found."}), {"persist": False, "calculate": None})
        except (ValueError, StaleResult) as exc:
            return (*self._refuse(exc), {"persist": False, "calculate": None})
        except Exception:
            traceback.print_exc()
            return (*_pack(400, {"error": "This operation could not finish. Saved work is retained; check the input and try again."}),
                    {"persist": False, "calculate": None})

    def _authorized(self, headers):
        supplied = headers.get("x-dsf-token", "")
        return isinstance(supplied, str) and supplied == self.workspace.token

    def _get(self, target, headers):
        route = urlsplit(target)
        if route.path == "/api/boot":
            with self.workspace.store._connection() as db:
                books = [dict(row) for row in db.execute("SELECT sha,label FROM workbooks ORDER BY created DESC")]
            return _pack(200, {
                "token": self.workspace.token,
                "title": self.workspace.args.edition_title,
                "note": self.workspace.args.edition_note,
                "example_available": True,
                "example_requires_download": not self.official_example_cached(),
                "example_label": self.workspace.args.example_label,
                "illustrative_example": True,
                "workbooks": books,
            })
        if not self._authorized(headers):
            return _pack(403, {"error": "Reload this local application tab."})
        query = parse_qs(route.query)
        try:
            if route.path == "/api/workbook":
                return _pack(200, self.workspace.context(query["sha"][0]))
            if route.path == "/api/job":
                with self.workspace.job_lock:
                    job = dict(self.workspace.jobs.get(
                        query["id"][0],
                        {"status": "interrupted", "message": "The application restarted. Recalculate the saved scenario."}))
                return _pack(200, job)
            if route.path == "/api/scenario":
                from lic_dsf import CONTRACT_VERSION, engine_identity
                scenario_id = query["id"][0]
                try:
                    run = self.workspace.store.current_run(
                        scenario_id, engine_identity=engine_identity(), contract_version=CONTRACT_VERSION)
                except StaleResult:
                    run = None
                return _pack(200, {"scenario": self.workspace.store.get_scenario(scenario_id), "run": run,
                                    "reasoning": self.workspace.store.reasoning_history(scenario_id)})
            return _pack(404, {"error": "Not found."})
        except (ValueError, StaleResult):
            raise
        except Exception:
            return _pack(400, {"error": "The saved item could not be loaded. Refresh the workspace or upload the original again."})

    def _post(self, target, body, headers):
        if not self._authorized(headers):
            return (*_pack(403, {"error": "Reload this local application tab."}), {"persist": False, "calculate": None})
        route = urlsplit(target).path
        limit = MAX_UPLOAD if route == "/api/upload" else 1024 * 1024
        if not body or len(body) > limit:
            return (*_pack(413, {"error": "The request is empty or too large."}), {"persist": False, "calculate": None})
        if route == "/api/upload":
            return (*_pack(200, self.workspace.ingest(body, headers.get("x-workbook-name", "Uploaded workbook"))),
                    {"persist": True, "calculate": None})
        data = json.loads(body, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Use finite numbers.")))
        if not isinstance(data, dict):
            raise ValueError("Use a workspace request object.")
        if route == "/api/example":
            return (*_pack(200, self.load_example()), {"persist": True, "calculate": None})
        if route == "/api/save":
            from lic_dsf import normalize_scenario
            if len(data.get("share_label", "Scenario")) > 40:
                raise ValueError("Use a shared chart label of at most 40 characters.")
            info = self.workspace.inspection(data["workbook_sha"])
            definition = normalize_scenario(data["definition"], info["input_years"])
            saved = self.workspace.store.save_scenario(
                data["workbook_sha"], data["name"], definition,
                scenario_id=data.get("scenario_id"), expected_revision=data.get("expected_revision"),
                share_label=data.get("share_label", "Scenario"),
                shared_rationale=data.get("shared_rationale"))
            return (*_pack(200, saved), {"persist": True, "calculate": None})
        if route == "/api/reasoning":
            return (*_pack(200, {"id": self.workspace.store.add_reasoning(data["scenario_id"], data["text"])}),
                    {"persist": True, "calculate": None})
        if route == "/api/chart-context":
            if set(data) != {"workbook_sha", "label", "expected_revision"}:
                raise ValueError("Provide a workbook, chart label and its expected revision.")
            return (*_pack(200, self.workspace.store.save_chart_context(
                data["workbook_sha"], data["label"], expected_revision=data["expected_revision"])),
                    {"persist": True, "calculate": None})
        if route == "/api/chart-text":
            if set(data) != {"workbook_sha", "labels", "heading", "expected_context_revision"}:
                raise ValueError("Provide the workbook, legend labels, heading and expected context revision.")
            return (*_pack(200, self.workspace.store.save_chart_text(
                data["workbook_sha"], data["labels"], data["heading"],
                expected_context_revision=data["expected_context_revision"])),
                    {"persist": True, "calculate": None})
        if route == "/api/calculate":
            job_id = self.begin_calculation(data["scenario_id"])
            return (*_pack(202, {"job_id": job_id}), {"persist": False, "calculate": job_id})
        if route == "/api/compare":
            return (*_pack(200, shareable(self.workspace.comparison(checked_comparison_request(data)))),
                    {"persist": False, "calculate": None})
        if route == "/api/export":
            return (*self._export(data), {"persist": False, "calculate": None})
        return (*_pack(404, {"error": "Not found."}), {"persist": False, "calculate": None})

    def _export(self, data):
        comparison = shareable(self.workspace.comparison(checked_comparison_request(data, export=True)))
        fmt = data.get("format", "json")
        if fmt == "json":
            return _pack(200, canonical(comparison).encode(), "application/octet-stream")
        if fmt == "zip":
            from lic_dsf.briefing_pack import render_pack
            return _pack(200, render_pack(comparison), "application/zip")
        if fmt == "xlsx":
            from lic_dsf.briefing_pack import tables, workbook_bytes
            return _pack(200, workbook_bytes(tables(comparison), comparison),
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        if data.get("metric") is not None:
            from lic_dsf.charts import render_indicator
            body = render_indicator(comparison, data["metric"], data.get("view"), fmt)
            return _pack(200, body, "image/svg+xml" if fmt == "svg" else "image/png")
        if fmt not in ("png", "pdf") or data.get("view") not in ("standard", "briefing"):
            raise ValueError("Choose a chart view and supported export format.")
        from lic_dsf.charts import render_comparison
        body = render_comparison(comparison, view=data["view"], format=fmt)
        return _pack(200, body, "image/png" if fmt == "png" else "application/pdf")

    def load_example(self):
        cached = self.workspace.uploads / (OFFICIAL_EXAMPLE_SHA + ".xlsm")
        if self.official_stage.is_file() and not cached.is_file():
            payload = self.official_stage.read_bytes()
            self.official_stage.unlink()
            cached.write_bytes(verify_official_example(payload))
        return self.workspace.load_example()

    def begin_calculation(self, scenario_id):
        case = self.workspace.store.get_scenario(scenario_id)
        self.workspace.path(case["workbook_sha"])
        import uuid
        with self.workspace.job_lock:
            if any(job["status"] == "running" for job in self.workspace.jobs.values()):
                raise ValueError("A calculation is already running. Your saved inputs are retained.")
            job_id = uuid.uuid4().hex
            self.workspace.jobs[job_id] = {
                "status": "running", "scenario_id": scenario_id, "revision": case["revision"]}
        return job_id

    def run_calculation(self, job_id):
        from lic_dsf import calculate
        job = self.workspace.jobs.get(job_id)
        if not job or job.get("status") != "running":
            return
        scenario_id = job["scenario_id"]
        revision = job["revision"]
        try:
            case = self.workspace.store.get_scenario(scenario_id)
            path = self.workspace.path(case["workbook_sha"])
            result = calculate(str(path), case["definition"], expected_sha256=case["workbook_sha"])
            run_id = self.workspace.store.record_run(scenario_id, result, expected_revision=revision)
            finished = {"status": "complete", "run_id": run_id, "scenario_id": scenario_id, "evidence": result["evidence"]}
        except Exception as exc:
            message = (str(exc) if isinstance(exc, (ValueError, StaleResult)) and len(str(exc)) < 400
                       and "/" not in str(exc) and "\\" not in str(exc)
                       else "Calculation could not finish. The saved scenario is retained.")
            finished = {"status": "failed", "message": message, "scenario_id": scenario_id}
        with self.workspace.job_lock:
            self.workspace.jobs[job_id] = finished

    @staticmethod
    def _refuse(exc):
        message = str(exc)
        conflict = isinstance(exc, StaleResult) and message == "The chart context changed. Reload it before saving or exporting."
        if len(message) > 400 or "/" in message or "\\" in message:
            message = "The request could not be completed. Your original workbook and saved scenarios are retained."
        return _pack(409 if conflict else 400, {"error": message})
