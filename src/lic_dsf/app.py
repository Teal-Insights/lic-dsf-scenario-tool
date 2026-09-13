"""Loopback-only analyst workspace. No hosted upload or external runtime assets."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import signal
import subprocess
import sys
import time
import tempfile
import threading
import uuid
from urllib.parse import parse_qs, urlsplit, unquote

from . import CONTRACT_VERSION, calculate, engine_identity, inspect_workbook, imported_scenario, zero_scenario, normalize_scenario
from .store import ScenarioStore, StaleResult, canonical
from .chart_context import validate_chart_context
from .rationale import normalize_rationale

MAX_UPLOAD = 25 * 1024 * 1024
OFFICIAL_EXAMPLE_SHA = "3a0a0b80c7cbc95ac953f25ecae0b437129d669ceb8aeefb54ab86dc8727ea86"


@contextmanager
def calculation_lease(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt
            handle.seek(0)
            if not handle.read(1):
                handle.write(b"0"); handle.flush()
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise ValueError("Another calculation is running. Try again when it finishes.") from exc
        else:
            import fcntl
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ValueError("Another calculation is running. Try again when it finishes.") from exc
        try:
            yield handle
        finally:
            if os.name == "nt":
                handle.seek(0); msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def shareable(comparison):
    """Explicit export fields; internal workbook names and reasoning never enter."""
    context = validate_chart_context(comparison.get("chart_context"), comparison["workbook_sha256"])
    output = {"format": "lic-dsf-comparison-v3", "workbook_sha256": comparison["workbook_sha256"],
              "chart_context": context, "comparator_id": comparison["comparator_id"], "runs": []}
    if comparison["workbook_sha256"] == OFFICIAL_EXAMPLE_SHA:
        output["workbook_provenance"] = {
            "source": "World Bank official IDA21 template",
            "illustrative": True,
            "disclosure": "Ghana-labelled sample data are purely illustrative; not an official Ghana forecast or DSA.",
            "source_url": "https://thedocs.worldbank.org/en/doc/f0ade6bcf85b6f98dbeb2c39a2b7770c-0360012025/new-lic-dsf-template",
        }
    else:
        output["workbook_provenance"] = {"source": "User-supplied workbook", "illustrative": None,
            "disclosure": "Input ownership and analytical interpretation are supplied by the analyst."}
    for run in comparison["runs"]:
        r = run["result"]
        if r["evidence"]["calculation"] != "computed_unverified":
            raise ValueError("Resolve the calculation findings before exporting this result.")
        output["runs"].append({"scenario_id": run["scenario_id"], "share_label": run["share_label"],
            "revision": run["revision"], "result_hash": run["result_hash"],
            "shared_rationale": normalize_rationale(run.get("shared_rationale", {})),
            "result": {key: r[key] for key in ("workbook_sha256", "contract_version", "engine_identity",
                "scenario", "scenario_hash", "first_projection_year", "input_years", "points", "thresholds", "evidence", "warnings")}})
    return output


class Workspace:
    def __init__(self, args):
        self.args = args
        self.directory = Path(args.data_dir).expanduser().resolve()
        self.store = ScenarioStore(self.directory)
        self.uploads = self.directory / "workbooks"
        self.uploads.mkdir(mode=0o700, exist_ok=True)
        self.token = secrets.token_urlsafe(32)
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="calculation")
        self.jobs = {}
        self.job_lock = threading.Lock()
        self.calculation_lock = Path(args.calculation_lock) if args.calculation_lock else self.directory / "calculation.lock"

    def path(self, sha):
        if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
            raise ValueError("Select a registered workbook.")
        path = self.uploads / (sha + ".xlsm")
        if not path.is_file() or path.is_symlink():
            raise ValueError("The workbook is no longer available. Upload it again.")
        return path

    def ingest(self, payload, label):
        if not payload or len(payload) > MAX_UPLOAD:
            raise ValueError("Choose a workbook smaller than 25 MB.")
        sha = hashlib.sha256(payload).hexdigest()
        fd, temporary = tempfile.mkstemp(suffix=".xlsm", dir=self.uploads)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload); handle.flush(); os.fsync(handle.fileno())
            inspection = inspect_workbook(temporary)
            if inspection["compatibility"]["status"] != "supported":
                return {"inspection": inspection, "accepted": False}
            destination = self.uploads / (sha + ".xlsm")
            try:
                os.link(temporary, destination)
            except FileExistsError:
                if destination.is_symlink() or hashlib.sha256(destination.read_bytes()).hexdigest() != sha:
                    raise ValueError("The local workbook copy failed its integrity check.")
            safe_label = Path(unquote(str(label)).replace("\\", "/")).name[:300] or "Uploaded workbook"
            self.store.register_workbook(sha, safe_label)
            return {"inspection": inspection, "accepted": True}
        finally:
            Path(temporary).unlink(missing_ok=True)

    def context(self, sha):
        info = inspect_workbook(self.path(sha))
        if info["workbook_sha256"] != sha:
            raise ValueError("The local workbook changed. Upload the original again.")
        from .ida21 import METRICS, OFFSETS, cell
        import openpyxl
        workbook = openpyxl.load_workbook(self.path(sha), read_only=True, data_only=True, keep_links=False)
        try:
            preview = [{"metric": metric, "year": info["first_projection_year"] + offset,
                        "units": units, "reference_baseline": workbook[sheet][cell(col + offset, base)].value}
                       for metric, title, units, sheet, base, custom, col, header in METRICS for offset in OFFSETS]
        finally:
            workbook.close()
        return {"inspection": info, "scenarios": self.store.list_scenarios(sha), "baseline_preview": preview,
                "chart_context": self.store.get_chart_context(sha),
                "baseline_preview_evidence": "saved_workbook_values_not_recalculated",
                "imported": imported_scenario(info), "zero": zero_scenario(info)}

    def start_calculation(self, scenario_id):
        case = self.store.get_scenario(scenario_id)
        path = self.path(case["workbook_sha"])
        with self.job_lock:
            if any(job["status"] == "running" for job in self.jobs.values()):
                raise ValueError("A calculation is already running. Your saved inputs are retained.")
            job_id = uuid.uuid4().hex
            self.jobs[job_id] = {"status": "running", "scenario_id": scenario_id, "revision": case["revision"]}
        def execute():
            try:
                job_directory = self.directory / "jobs" / job_id
                job_directory.mkdir(parents=True, mode=0o700)
                input_path = job_directory / "request.json"
                input_path.write_text(canonical({"workbook": str(path), "workbook_sha256": case["workbook_sha"], "scenario": case["definition"], "parent_pid": os.getpid(), "deadline_utc": time.time() + workspace_timeout(self.args)}), encoding="utf-8")
                input_path.chmod(0o600)
                with calculation_lease(self.calculation_lock) as lease:
                    kwargs = {"start_new_session": True} if os.name != "nt" else {}
                    if os.name != "nt":
                        kwargs["pass_fds"] = (lease.fileno(),)
                    with (job_directory / "worker.log").open("wb") as log:
                        child = subprocess.Popen([sys.executable, "-B", "-m", "lic_dsf.worker", str(input_path)],
                                                 stdout=log, stderr=log, **kwargs)
                        try:
                            child.wait(timeout=workspace_timeout(self.args))
                        except BaseException:
                            if child.poll() is None:
                                if os.name != "nt":
                                    os.killpg(child.pid, signal.SIGTERM)
                                else:
                                    child.terminate()
                                try:
                                    child.wait(timeout=5)
                                except subprocess.TimeoutExpired:
                                    if os.name != "nt":
                                        os.killpg(child.pid, signal.SIGKILL)
                                    else:
                                        child.kill()
                                    child.wait(timeout=5)
                            raise ValueError("The calculation exceeded its time limit. Saved inputs are retained.")
                    if child.returncode != 0:
                        error_file = job_directory / "error.json"
                        code = json.loads(error_file.read_text(encoding="utf-8")).get("code") if error_file.is_file() else None
                        raise ValueError("Calculation could not finish" + (": " + code if code else ". Saved inputs are retained."))
                    result = json.loads((job_directory / "result.json").read_text(encoding="utf-8"))
                run_id = self.store.record_run(scenario_id, result, expected_revision=case["revision"])
                finished = {"status": "complete", "run_id": run_id, "scenario_id": scenario_id, "evidence": result["evidence"]}
            except Exception as exc:
                # Only stable application messages leave this boundary; no traceback/file paths.
                message = str(exc) if isinstance(exc, (ValueError, StaleResult)) and len(str(exc)) < 400 and "/" not in str(exc) else "Calculation could not finish. The saved scenario is retained."
                finished = {"status": "failed", "message": message, "scenario_id": scenario_id}
            with self.job_lock:
                self.jobs[job_id] = finished
        self.executor.submit(execute)
        return {"job_id": job_id}

    def comparison(self, data):
        return self.store.comparison(data["scenario_ids"], data["comparator_id"],
            engine_identity=engine_identity(), contract_version=CONTRACT_VERSION,
            workbook_sha=data.get("workbook_sha"),
            expected_chart_context_revision=data.get("expected_chart_context_revision"))


def checked_comparison_request(data, *, export=False):
    """HTTP callers must name the source and outward context they actually saw."""
    required = {"scenario_ids", "comparator_id", "workbook_sha", "expected_chart_context_revision"}
    allowed = required | ({"format", "view", "metric"} if export else set())
    if not isinstance(data, dict) or not required.issubset(data):
        raise ValueError("Reload this application and reopen the workbook before comparing or exporting.")
    if set(data) - allowed:
        raise ValueError("Use the saved chart label; comparison requests cannot override export text.")
    sha = data["workbook_sha"]
    revision = data["expected_chart_context_revision"]
    if (not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha)
            or type(revision) is not int or revision < 0):
        raise ValueError("Reload this application and reopen the workbook before comparing or exporting.")
    return data


def workspace_timeout(args):
    return max(1, min(float(args.calculation_timeout), 600))


def handler_for(workspace):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def send(self, status, payload, content_type="application/json", attachment=None):
            body = canonical(payload).encode() if content_type == "application/json" else payload
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' blob:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            if attachment:
                self.send_header("Content-Disposition", 'attachment; filename="' + attachment + '"')
            self.end_headers(); self.wfile.write(body)

        def trusted_host(self):
            return self.headers.get("Host") in {"127.0.0.1:" + str(self.server.server_port), "localhost:" + str(self.server.server_port)}

        def authorized(self):
            origin = self.headers.get("Origin")
            allowed = {"http://127.0.0.1:" + str(self.server.server_port), "http://localhost:" + str(self.server.server_port)}
            return self.trusted_host() and (not origin or origin in allowed) and secrets.compare_digest(self.headers.get("X-DSF-Token", ""), workspace.token)

        def do_GET(self):
            if not self.trusted_host():
                return self.send(403, {"error": "Use the local application address."})
            route = urlsplit(self.path)
            if route.path == "/":
                return self.send(200, (Path(__file__).parent / "web.html").read_bytes(), "text/html; charset=utf-8")
            if route.path in ('/fonts/Inter-Regular.otf', '/fonts/Inter-SemiBold.otf', '/fonts/IBMPlexSerif-SemiBold.otf'):
                return self.send(200, (Path(__file__).parent / route.path.lstrip('/')).read_bytes(), 'font/otf')
            # Browser same-origin policy and Host validation protect this boot token.
            if route.path == "/api/boot":
                with workspace.store._connection() as db:
                    books = [dict(r) for r in db.execute("SELECT sha,label FROM workbooks ORDER BY created DESC")]
                return self.send(200, {"token": workspace.token, "title": workspace.args.edition_title,
                    "note": workspace.args.edition_note, "example_available": bool(workspace.args.example),
                    "example_label": workspace.args.example_label, "illustrative_example": workspace.args.illustrative_example,
                    "workbooks": books})
            if not self.authorized():
                return self.send(403, {"error": "Reload this local application tab."})
            query = parse_qs(route.query)
            try:
                if route.path == "/api/workbook":
                    return self.send(200, workspace.context(query["sha"][0]))
                if route.path == "/api/job":
                    with workspace.job_lock:
                        job = dict(workspace.jobs.get(query["id"][0], {"status": "interrupted", "message": "The application restarted. Recalculate the saved scenario."}))
                    return self.send(200, job)
                if route.path == "/api/scenario":
                    sid = query["id"][0]
                    try:
                        run = workspace.store.current_run(sid, engine_identity=engine_identity(), contract_version=CONTRACT_VERSION)
                    except StaleResult:
                        run = None
                    return self.send(200, {"scenario": workspace.store.get_scenario(sid), "run": run,
                        "reasoning": workspace.store.reasoning_history(sid)})
                return self.send(404, {"error": "Not found."})
            except Exception:
                return self.send(400, {"error": "The saved item could not be loaded. Refresh the workspace or upload the original again."})

        def do_POST(self):
            if not self.authorized():
                return self.send(403, {"error": "Reload this local application tab."})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                limit = MAX_UPLOAD if self.path == "/api/upload" else 1024 * 1024
                if length <= 0 or length > limit:
                    return self.send(413, {"error": "The request is empty or too large."})
                self.connection.settimeout(30)
                payload = self.rfile.read(length)
                if len(payload) != length:
                    raise ValueError("The upload was interrupted. Try again.")
                if self.path == "/api/upload":
                    return self.send(200, workspace.ingest(payload, self.headers.get("X-Workbook-Name", "Uploaded workbook")))
                data = json.loads(payload, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Use finite numbers.")))
                if not isinstance(data, dict):
                    raise ValueError("Use a workspace request object.")
                if self.path == "/api/example":
                    if not workspace.args.example:
                        raise ValueError("No example is configured. Upload your workbook.")
                    example = Path(workspace.args.example).read_bytes()
                    expected = workspace.args.example_sha256 or (OFFICIAL_EXAMPLE_SHA if workspace.args.illustrative_example else None)
                    if expected and hashlib.sha256(example).hexdigest() != expected:
                        raise ValueError("The example differs from its configured source identity. Upload a supported workbook or restore the exact example.")
                    return self.send(200, workspace.ingest(example, workspace.args.example_label))
                if self.path == "/api/save":
                    if len(data.get("share_label", "Scenario")) > 40:
                        raise ValueError("Use a shared chart label of at most 40 characters.")
                    info = inspect_workbook(workspace.path(data["workbook_sha"]))
                    definition = normalize_scenario(data["definition"], info["input_years"])
                    return self.send(200, workspace.store.save_scenario(data["workbook_sha"], data["name"], definition,
                        scenario_id=data.get("scenario_id"), expected_revision=data.get("expected_revision"), share_label=data.get("share_label", "Scenario"),
                        shared_rationale=data.get("shared_rationale")))
                if self.path == "/api/reasoning":
                    return self.send(200, {"id": workspace.store.add_reasoning(data["scenario_id"], data["text"])})
                if self.path == "/api/chart-context":
                    if set(data) != {"workbook_sha", "label", "expected_revision"}:
                        raise ValueError("Provide a workbook, chart label and its expected revision.")
                    return self.send(200, workspace.store.save_chart_context(data["workbook_sha"], data["label"],
                        expected_revision=data["expected_revision"]))
                if self.path == "/api/chart-text":
                    if set(data) != {"workbook_sha", "labels", "heading", "expected_context_revision"}:
                        raise ValueError("Provide the workbook, legend labels, heading and expected context revision.")
                    return self.send(200, workspace.store.save_chart_text(data["workbook_sha"], data["labels"], data["heading"],
                        expected_context_revision=data["expected_context_revision"]))
                if self.path == "/api/calculate":
                    return self.send(202, workspace.start_calculation(data["scenario_id"]))
                if self.path == "/api/compare":
                    return self.send(200, shareable(workspace.comparison(checked_comparison_request(data))))
                if self.path == "/api/export":
                    comparison = shareable(workspace.comparison(checked_comparison_request(data, export=True)))
                    fmt = data.get("format", "json")
                    if fmt == "json":
                        return self.send(200, canonical(comparison).encode(), "application/octet-stream", "scenario-comparison.json")
                    if fmt == "zip":
                        from .briefing_pack import render_pack
                        return self.send(200, render_pack(comparison), "application/zip", "lic-dsf-briefing-packet.zip")
                    if fmt == "xlsx":
                        from .briefing_pack import tables, workbook_bytes
                        return self.send(200, workbook_bytes(tables(comparison), comparison), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "scenario-tables.xlsx")
                    if data.get("metric") is not None:
                        from .charts import render_indicator
                        body = render_indicator(comparison, data['metric'], data.get('view'), fmt)
                        return self.send(200, body, 'image/svg+xml' if fmt == 'svg' else 'image/png', 'scenario-chart.' + fmt)
                    if fmt not in ("png", "pdf") or data.get("view") not in ("standard", "briefing"):
                        raise ValueError("Choose a chart view and supported export format.")
                    from .charts import render_comparison
                    body = render_comparison(comparison, view=data["view"], format=fmt)
                    return self.send(200, body, "image/png" if fmt == "png" else "application/pdf", "scenario-comparison." + fmt)
                return self.send(404, {"error": "Not found."})
            except (ValueError, StaleResult) as exc:
                message = str(exc)
                conflict = isinstance(exc, StaleResult) and message == "The chart context changed. Reload it before saving or exporting."
                if len(message) > 400 or "/" in message or "\\" in message:
                    message = "The request could not be completed. Your original workbook and saved scenarios are retained."
                return self.send(409 if conflict else 400, {"error": message})
            except Exception:
                return self.send(400, {"error": "This operation could not finish. Saved work is retained; check the input and try again."})
    return Handler


def main():
    parser = argparse.ArgumentParser(description="Run the local LIC-DSF scenario workspace.")
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--port", type=int, default=8526)
    parser.add_argument("--open-browser", action="store_true", help="Open the local workspace in your default browser.")
    parser.add_argument("--example")
    parser.add_argument("--example-sha256")
    parser.add_argument("--example-label", default="Official IDA21 illustrative example")
    parser.add_argument("--illustrative-example", action="store_true")
    parser.add_argument("--edition-title", default="LIC-DSF Scenario Analysis Tool")
    parser.add_argument("--edition-note", default="")
    parser.add_argument("--calculation-lock")
    parser.add_argument("--calculation-timeout", type=float, default=240)
    args = parser.parse_args()
    if args.port != 0 and not 1024 <= args.port <= 65535:
        parser.error("Use a local port between 1024 and 65535, or 0 to choose an available port.")
    workspace = Workspace(args)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_for(workspace))
    args.port = server.server_port
    server.daemon_threads = True
    print("Open http://127.0.0.1:" + str(args.port), flush=True)
    try:
        if args.open_browser:
            import webbrowser
            webbrowser.open("http://127.0.0.1:" + str(args.port))
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        workspace.executor.shutdown(wait=True, cancel_futures=True)


if __name__ == "__main__":
    main()
