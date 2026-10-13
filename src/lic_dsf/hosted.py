"""Single-process WSGI entry point for the ephemeral official-example pilot.

The WSGI server owns HTTP parsing. The existing application handler is invoked
only as an in-memory route adapter after hosted authorization and admission.
Never start the desktop HTTP server for this mode.
"""
from __future__ import annotations
import copy
from collections import deque
import tempfile
import hashlib
import io
import json
import math
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import threading
import time
import uuid
from http.cookies import SimpleCookie
from http import HTTPStatus
from types import SimpleNamespace
from urllib.parse import urlsplit

from .app import Workspace, OFFICIAL_EXAMPLE_SHA, handler_for
from .store import canonical
from .engine import digest

MAX_BODY = 131072
MAX_SESSIONS = 12
MAX_REQUESTS = 600
MAX_MUTATIONS = 60
MAX_JOBS = 8
MAX_EXPORTS = 30
MAX_JSON_DEPTH = 32
BUSY_MESSAGE = 'A calculation or export is running. Your saved work is retained. Please retry shortly.'
TTL = 3600
DISCLOSURE = ('Illustrative online experiment. Assumptions, labels and explanations are processed on this server. '
              'Use only illustrative, non-confidential inputs. The example uses illustrative data from the IMF and World Bank LIC-DSF template and does not represent any actual country. '
              'Access expires one hour after entry. Server cleanup is targeted within another 75 seconds, or when you delete the visit; work is also lost on service restart. '
              'Download scenario files to keep your inputs. Downloaded files remain on your device. '
              'Own-workbook use and private journals are available only in the local app.')
POSTS = {'/api/example', '/api/save', '/api/chart-context', '/api/chart-text', '/api/calculate', '/api/compare', '/api/export', '/api/delete', '/api/export-jobs', '/api/export-cancel'}
GETS = {'/api/boot', '/api/workbook', '/api/scenario', '/api/job', '/api/export-status', '/api/export-result', '/api/export-current'}


class HostedWorkspace(Workspace):
    def __init__(self, owner, directory):
        self.owner = owner
        args = SimpleNamespace(data_dir=str(directory), calculation_lock=None, calculation_timeout=180,
            example=str(owner.workbook), example_sha256=OFFICIAL_EXAMPLE_SHA,
            example_label='Official illustrative example', illustrative_example=True,
            edition_title='LIC-DSF Scenario Analysis Tool — illustrative online experiment', edition_note=DISCLOSURE)
        super().__init__(args)
        self.created = owner.clock()
        self.requests = self.mutations = self.exports = 0
        self.child = None
        self.export_child = None
        self.closed = False

    def load_example(self):
        # Hosting never downloads or populates a local-app workbook cache.
        return self.ingest(self.owner.workbook.read_bytes(), self.args.example_label)

    def inspection(self, sha):
        self.path(sha)
        return copy.deepcopy(self.owner.inspection)

    def context(self, sha):
        self.path(sha)
        if self.owner.context_cache is None:
            self.owner.context_cache = {key: value for key, value in super().context(sha).items()
                                        if key not in {'scenarios', 'chart_context'}}
        result = copy.deepcopy(self.owner.context_cache)
        result['scenarios'] = self.store.list_scenarios(sha)
        result['chart_context'] = self.store.get_chart_context(sha)
        return result

    def check_export_quota(self, data):
        # Count completed responses only. Reserve the final slot for a full packet;
        # busy/invalid/failed attempts do not consume it. The request cap still applies.
        packet = data.get('format') == 'zip'
        if self.exports >= MAX_EXPORTS or (not packet and self.exports >= MAX_EXPORTS - 1):
            raise ValueError('Chart and individual-download limit reached. Use Download briefing packet for the reserved final slot.'
                             if self.exports < MAX_EXPORTS else 'This visit has used all 30 chart and download slots.')
    def bounded_export(self, comparison, data, *, count_response=True):
        self.check_export_quota(data)
        if not self.owner.compute.acquire(blocking=False):
            raise ValueError(BUSY_MESSAGE)
        try:
            if data.get('format', 'json') == 'json':
                result = canonical(comparison).encode(), 'application/octet-stream', 'scenario-comparison.json'
            else:
                result = self._render_export(comparison, data)
            if self.closed:
                raise ValueError('The visit ended while the export was running. Return to the entry page.')
            if count_response:
                self.exports += 1
            return result
        finally:
            self.owner.compute.release()

    def _render_export(self, comparison, data):
        with tempfile.TemporaryDirectory(dir=self.directory, prefix='export-') as temporary:
            directory = Path(temporary)
            (directory / 'request.json').write_text(canonical({'comparison': comparison, 'data': data, 'parent_pid': os.getpid(), 'deadline_utc': time.time() + 60}))
            child = subprocess.Popen([sys.executable, '-B', '-m', 'lic_dsf.hosted_export', temporary],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            self.export_child = child
            # The request owns this lock. Release it while the bounded leaf runs so
            # other visitors can receive busy responses and expiry/deletion can act.
            self.owner.lock.release()
            try:
                try:
                    child.wait(timeout=60)
                except BaseException:
                    child.kill(); child.wait(timeout=5)
                    raise ValueError('The export exceeded its time limit.')
            finally:
                self.owner.lock.acquire()
                self.export_child = None
            if self.closed:
                raise ValueError('The visit ended while the export was running. Return to the entry page.')
            if child.returncode:
                raise ValueError('The export could not finish within the service limits.')
            ctype, name = json.loads((directory / 'meta.json').read_text())
            return (directory / 'body').read_bytes(), ctype, name

    def path(self, sha):
        if sha != OFFICIAL_EXAMPLE_SHA:
            raise ValueError('Only the approved illustrative workbook is available online.')
        return self.owner.workbook

    def ingest(self, payload, label):
        # Defense in depth: even internal callers cannot register different bytes.
        if hashlib.sha256(payload).hexdigest() != OFFICIAL_EXAMPLE_SHA:
            raise ValueError('Only the approved illustrative workbook is available online.')
        self.store.register_workbook(OFFICIAL_EXAMPLE_SHA, 'Official illustrative example')
        return {'accepted': True, 'inspection': self.owner.inspection}

    def start_calculation(self, scenario_id):
        case = self.store.get_scenario(scenario_id)  # belongs to this visitor's database
        if len(self.jobs) >= MAX_JOBS:
            raise ValueError('This visit has reached its eight-calculation limit.')
        prepared = self.owner.prepared_cache.lookup(case['workbook_sha'], case['definition']) if self.owner.prepared_cache else None
        if prepared is not None:
            job_id = uuid.uuid4().hex
            run = self.store.record_run(scenario_id, prepared, expected_revision=case['revision'])
            self.jobs[job_id] = {'status': 'complete', 'run_id': run, 'scenario_id': scenario_id,
                                'evidence': prepared['evidence']}
            return {'job_id': job_id}
        if getattr(self.owner, 'export_queue', None) and self.owner.export_queue.has_waiting():
            raise ValueError('Chart exports are waiting. Saved inputs are retained; retry this calculation shortly.')
        if not self.owner.compute.acquire(blocking=False):
            raise ValueError(BUSY_MESSAGE)
        job_id = uuid.uuid4().hex
        self.jobs[job_id] = {'status': 'running', 'scenario_id': scenario_id}
        def execute():
            directory = self.directory / 'jobs' / job_id
            try:
                with self.owner.lock:
                    if self.closed:
                        return
                    directory.mkdir(parents=True, mode=0o700)
                request = directory / 'request.json'
                request.write_text(canonical({'workbook': str(self.path(case['workbook_sha'])),
                    'workbook_sha256': case['workbook_sha'], 'scenario': case['definition'],
                    'parent_pid': os.getpid(), 'deadline_utc': time.time() + 180}), encoding='utf-8')
                request.chmod(0o600)
                with self.owner.lock:
                    if self.closed:
                        return
                    self.child = subprocess.Popen([sys.executable, '-B', '-m', 'lic_dsf.hosted_worker', str(request)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                try:
                    self.child.wait(timeout=180)
                except subprocess.TimeoutExpired:
                    self.child.kill(); self.child.wait(timeout=5)
                    raise ValueError('Calculation time limit reached.')
                with self.owner.lock:
                    if self.closed:
                        return
                    if self.child.returncode:
                        raise ValueError('Calculation could not finish within the service limits.')
                    result = json.loads((directory / 'result.json').read_text())
                    source_hash = result.pop('run_hash')
                    result['evidence']['execution'] = {
                        'mode': 'fresh_calculation_for_visit', 'fresh_calculation_for_visit': True,
                        'calculated_result_hash': source_hash,
                    }
                    result['run_hash'] = digest(result)
                    run = self.store.record_run(scenario_id, result, expected_revision=case['revision'])
                    self.jobs[job_id] = {'status': 'complete', 'run_id': run, 'scenario_id': scenario_id, 'evidence': result['evidence']}
            except Exception:
                with self.owner.lock:
                    if not self.closed:
                        self.jobs[job_id] = {'status': 'failed', 'message': 'Calculation could not finish within the service limits. Saved inputs are retained.'}
            finally:
                shutil.rmtree(directory, ignore_errors=True)
                self.owner.compute.release()
        try:
            future = self.executor.submit(execute)
        except Exception:
            self.owner.compute.release()
            raise
        future.add_done_callback(lambda done: self.owner.compute.release() if done.cancelled() else None)
        return {'job_id': job_id}

    def close(self):
        self.closed = True
        if getattr(self.owner, 'export_queue', None):
            self.owner.export_queue.cancel_visitor(self)
        for child in (self.child, getattr(self, 'export_child', None)):
            if child and child.poll() is None:
                child.kill(); child.wait(timeout=5)
        self.executor.shutdown(wait=False, cancel_futures=True)
        shutil.rmtree(self.directory)


class HostedApplication:
    def __init__(self, root, workbook, origin, *, clock=time.monotonic, sweep=True, allow_loopback_http=False, prepare_teaching=False, workshop_test=False):
        from . import inspect_workbook
        self.origin = origin.rstrip('/')
        parsed = urlsplit(self.origin)
        local_test = allow_loopback_http and parsed.scheme == 'http' and parsed.hostname == 'localhost'
        if (parsed.scheme != 'https' and not local_test) or not parsed.netloc or parsed.path:
            raise ValueError('Configure one exact HTTPS origin.')
        self.host = parsed.netloc
        self.workbook = Path(workbook).resolve()
        if hashlib.sha256(self.workbook.read_bytes()).hexdigest() != OFFICIAL_EXAMPLE_SHA:
            raise ValueError('The official workbook identity does not match.')
        self.inspection = inspect_workbook(self.workbook)
        self.max_sessions, self.max_starts, self.max_hits = (25, 50, 1200) if workshop_test else (MAX_SESSIONS, 24, 240)
        self.prepared_cache = None
        if workshop_test and not prepare_teaching:
            raise ValueError('Provisional workshop mode requires prepared teaching results.')
        self.page = hosted_page()  # Fail startup if local-template copy has drifted.
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Hold an exclusive process lease before cleanup; never operate two replicas.
        import fcntl
        self.lease = (self.root / 'hosted.lock').open('a+b')
        fcntl.flock(self.lease.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.visitors = self.root / 'visitors'
        if self.visitors.exists():
            shutil.rmtree(self.visitors)
        self.visitors.mkdir(mode=0o700)
        self.clock = clock
        self.sessions = {}
        self.context_cache = None
        self.admissions = deque()
        self.hits = deque()
        self.lock = threading.RLock()
        self.compute = threading.BoundedSemaphore(1)
        self.stopped = threading.Event()
        self.cleanup_failed = False
        if prepare_teaching:
            try:
                from .hosted_cache import prepare
                self.prepared_cache = prepare(self.workbook, self.visitors)
            except BaseException:
                self.lease.close()
                raise
        from .hosted_queue import ExportQueue
        self.export_queue = ExportQueue(self)
        if sweep:
            threading.Thread(target=self._sweep, daemon=True).start()

    def _sweep(self):
        while not self.stopped.wait(5):
            with self.lock:
                try:
                    self.expire()
                except (OSError, subprocess.TimeoutExpired):
                    self.cleanup_failed = True

    def expire(self):
        for key, ws in list(self.sessions.items()):
            if self.clock() - ws.created >= TTL:
                ws.close(); del self.sessions[key]
        if getattr(self, 'export_queue', None):
            self.export_queue.expire()
        self.cleanup_failed = False

    def close(self):
        self.stopped.set()
        self.export_queue.stopping.set()
        self.export_queue.wake.set()
        with self.lock:
            for ws in self.sessions.values():
                ws.close()
            self.sessions.clear()
        self.export_queue.thread.join(timeout=5)
        if self.export_queue.thread.is_alive():
            raise RuntimeError('Export worker did not stop.')
        self.lease.close()

    def __call__(self, env, start_response):
        def respond(code, data, ctype='application/json', extra=()):
            if code in {429, 503}:
                extra = list(extra) + [('Retry-After', '3')]
            body = canonical(data).encode() if ctype == 'application/json' else data
            headers = [('Content-Type', ctype), ('Content-Length', str(len(body))), ('Cache-Control', 'no-store'),
                ('X-Content-Type-Options', 'nosniff'), ('Referrer-Policy', 'no-referrer'),
                ('Content-Security-Policy', "default-src 'self'; img-src 'self' blob:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"),
                ('Strict-Transport-Security', 'max-age=31536000')] + list(extra)
            start_response(str(code) + ' ' + HTTPStatus(code).phrase, headers)
            return [body]
        method, path = env.get('REQUEST_METHOD'), env.get('PATH_INFO', '')
        if env.get('HTTP_HOST') != self.host:
            return respond(403, {'error': 'Use the configured service address.'})
        if (method == 'GET' and path == '/' and env.get('HTTP_SEC_FETCH_MODE') == 'navigate'
                and env.get('HTTP_SEC_FETCH_DEST') == 'document'):
            return respond(200, landing(self.max_sessions, self.max_starts), 'text/html; charset=utf-8')
        origin = env.get('HTTP_ORIGIN')
        if (origin and origin != self.origin) or env.get('HTTP_SEC_FETCH_SITE') == 'cross-site':
            if (method == 'GET' and path == '/app'
                    and env.get('HTTP_SEC_FETCH_MODE') == 'navigate'
                    and env.get('HTTP_SEC_FETCH_DEST') == 'document'
                    and 'text/html' in env.get('HTTP_ACCEPT', '')):
                return respond(403, recovery_page(), 'text/html; charset=utf-8')
            return respond(403, {'error': 'Use this service in its own tab.'})
        if method == 'GET' and path == '/':
            return respond(200, landing(self.max_sessions, self.max_starts), 'text/html; charset=utf-8')
        if method == 'GET' and path.startswith('/fonts/') and path[7:] in {'Inter-Regular.otf', 'Inter-SemiBold.otf', 'IBMPlexSerif-SemiBold.otf'}:
            return respond(200, (Path(__file__).parent / path[1:]).read_bytes(), 'font/otf')
        if method == 'POST' and (origin != self.origin or env.get('CONTENT_TYPE') != 'application/json'):
            return respond(403, {'error': 'Use a same-origin JSON request.'})
        allowed = (method == 'GET' and path in GETS | {'/app'}) or (method == 'POST' and path in POSTS | {'/api/session'})
        if not allowed:
            return respond(404, {'error': 'This route is unavailable online. Own-workbook use stays local.'})
        payload = b''
        if method == 'POST':
            try:
                length = int(env.get('CONTENT_LENGTH', '0'))
            except ValueError:
                length = 0
            if not 0 < length <= MAX_BODY:
                return respond(413, {'error': 'Request size limit exceeded.'})
            payload = env['wsgi.input'].read(length)
            if len(payload) != length:
                return respond(400, {'error': 'Incomplete request.'})
            try:
                data = bounded_json(payload)
            except (ValueError, TypeError, RecursionError, UnicodeError):
                return respond(400, {'error': 'Use a valid finite JSON object with unique fields and nesting no deeper than 32 levels.'})
        # Serialize API admission, database operations and renderer access. Calculations
        # run in a single bounded child; no unbounded background queue is admitted.
        with self.lock:
            try:
                self.expire()
            except (OSError, subprocess.TimeoutExpired):
                self.cleanup_failed = True
                return respond(503, {'error': 'Temporary workspace cleanup is unavailable. Please return later.'})
            now = self.clock()
            while self.hits and self.hits[0] < now - 60:
                self.hits.popleft()
            if len(self.hits) >= self.max_hits and path not in {'/api/delete', '/api/export-cancel'}:
                return respond(429, {'error': 'Service request rate limit reached. Please wait a minute.'})
            if path not in {'/api/delete', '/api/export-cancel'}:
                self.hits.append(now)
            cookies = SimpleCookie()
            try:
                cookies.load(env.get('HTTP_COOKIE', ''))
                key = cookies['__Host-dsf'].value if '__Host-dsf' in cookies else ''
            except Exception:
                key = ''
            ws = self.sessions.get(key)
            if path == '/api/session':
                if payload != b'{"accept":true}':
                    return respond(400, {'error': 'Accept the illustrative server-processing disclosure first.'})
                if ws is None:
                    while self.admissions and self.admissions[0] < now - 3600:
                        self.admissions.popleft()
                    if len(self.admissions) >= self.max_starts:
                        return respond(429, {'error': 'Service visit-start limit reached. Please return later.'})
                    if len(self.sessions) >= self.max_sessions:
                        return respond(503, {'error': 'All visitor places are occupied. Please return later.'})
                    self.admissions.append(now)
                    key = secrets.token_urlsafe(32)
                    ws = HostedWorkspace(self, self.visitors / uuid.uuid4().hex)
                    self.sessions[key] = ws
                return respond(200, {'ready': True}, extra=[('Set-Cookie', '__Host-dsf=' + key + '; Path=/; Secure; HttpOnly; SameSite=Strict; Max-Age=3600')])
            if ws is None:
                if path == '/app':
                    return respond(401, recovery_page(), 'text/html; charset=utf-8')
                return respond(401, {'error': 'Visit expired or unavailable. Return to the entry page to begin again.'})
            ws.requests += 1
            if ws.requests > MAX_REQUESTS and path not in {'/api/delete', '/api/export-cancel'}:
                return respond(429, {'error': 'This visit has reached its request limit. Downloaded files remain on your device.'})
            if path == '/app':
                return respond(200, self.page, 'text/html; charset=utf-8')
            if path != '/api/boot' and not secrets.compare_digest(env.get('HTTP_X_DSF_TOKEN', ''), ws.token):
                return respond(403, {'error': 'Reload your visitor tab.'})
            if path == '/api/delete':
                ws.close(); del self.sessions[key]
                return respond(200, {'deleted': True}, extra=[('Set-Cookie', '__Host-dsf=; Path=/; Secure; HttpOnly; SameSite=Strict; Max-Age=0')])
            if method == 'POST' and path in {'/api/save', '/api/chart-context', '/api/chart-text'}:
                ws.mutations += 1
                if ws.mutations > MAX_MUTATIONS:
                    return respond(429, {'error': 'This visit has reached its saved-edit limit.'})
            if path in {'/api/compare', '/api/export', '/api/export-jobs'}:
                try:
                    if not isinstance(data, dict) or not isinstance(data.get('scenario_ids'), list) or not 1 <= len(data['scenario_ids']) <= 4:
                        raise ValueError()
                except (ValueError, TypeError):
                    return respond(400, {'error': 'Compare one to four calculated cases.'})
            if path == '/api/export-jobs':
                from .app import shareable, checked_comparison_request
                try:
                    request_key = data.get('request_key')
                    if not isinstance(request_key, str) or not 1 <= len(request_key) <= 64 or not all(c.isalnum() or c == '-' for c in request_key):
                        raise ValueError('Use a valid export request identifier.')
                    data = {k:v for k,v in data.items() if k != 'request_key'}
                    if not isinstance(data.get('format', 'json'), str) or data.get('format', 'json') not in {'json', 'svg', 'png', 'pdf', 'xlsx', 'zip'}:
                        raise ValueError('Choose a supported export format.')
                    if not all(isinstance(x, str) and 1 <= len(x) <= 64 for x in data.get('scenario_ids', [])) or not isinstance(data.get('comparator_id'), str):
                        raise ValueError('Use saved scenario identifiers from this visit.')
                    comparison = shareable(ws.comparison(checked_comparison_request(data, export=True)))
                    job_id = self.export_queue.submit(ws, comparison, copy.deepcopy(data), request_key)
                    if job_id is None:
                        return respond(503, {'error': 'The export queue is full. Please try again shortly.'})
                    return respond(202, {'job_id': job_id}, extra=[('Retry-After', '2')])
                except (ValueError, KeyError, TypeError) as error:
                    message = str(error) or 'The export could not be queued.'
                    if len(message) > 400 or '/' in message or '\\' in message:
                        message = 'The export could not be queued. Saved work is retained.'
                    return respond(409 if message == 'The chart context changed. Reload it before saving or exporting.' else 400, {'error': message})
                except Exception:
                    return respond(400, {'error': 'The export could not be queued. Saved work is retained; check the input.'})
            if path == '/api/export-current':
                key = self.export_queue.by_visitor.get(ws)
                state = self.export_queue.status(ws, key)
                return respond(200, state or {'status': 'none'}, extra=[('Retry-After', '2')])
            if path in {'/api/export-status', '/api/export-result', '/api/export-cancel'}:
                from urllib.parse import parse_qs
                key = data.get('job_id') if path == '/api/export-cancel' else parse_qs(env.get('QUERY_STRING', '')).get('id', [''])[0]
                if not isinstance(key, str) or not self.export_queue.own(ws, key):
                    return respond(404, {'error': 'This export is unavailable in this visit.'})
                if path == '/api/export-cancel':
                    self.export_queue.cancel(ws, key)
                    return respond(200, {'cancelled': True})
                state = self.export_queue.status(ws, key)
                if path == '/api/export-status':
                    return respond(200, state, extra=[('Retry-After', '2')])
                if state['status'] in {'queued', 'running'}:
                    return respond(503, {'error': 'Export is still waiting or running.'})
                if state['status'] != 'ready':
                    return respond(410, {'error': 'This export ended. Your saved scenarios remain available.'})
                try:
                    body, ctype, name = self.export_queue.take(ws, key)
                    return respond(200, body, ctype, [('Content-Disposition', 'attachment; filename="' + name + '"')])
                except ValueError as error:
                    return respond(400, {'error': str(error)})
            if path == '/api/export' and self.export_queue.has_waiting():
                return respond(429, {'error': 'Use the export queue while other exports are waiting.'})
            # Adapter invokes existing routes, never their socket/parser/authentication.
            handler_class = handler_for(ws)
            handler = handler_class.__new__(handler_class)
            handler.path = path + ('?' + env['QUERY_STRING'] if env.get('QUERY_STRING') else '')
            handler.headers = {'Content-Length': str(len(payload))}
            handler.rfile = io.BytesIO(payload)
            handler.connection = SimpleNamespace(settimeout=lambda value: None)
            handler.trusted_host = lambda: True
            handler.authorized = lambda: True
            output = []
            def send(code, data, ctype='application/json', attachment=None):
                if (ctype == 'application/json' and isinstance(data, dict) and
                        data.get('error') == 'The saved item could not be loaded. Refresh the workspace or upload the original again.'):
                    data = {'error': 'The saved item is unavailable in this visit. Reopen the official example or return to the entry page.'}
                output.extend(respond(code, data, ctype, [('Content-Disposition', 'attachment; filename="' + attachment + '"')] if attachment else []))
            handler.send = send
            if method == 'GET':
                handler.do_GET()
            else:
                handler.do_POST()
            return output


def bounded_json(payload):
    # Bound nesting before the recursive JSON decoder; brackets in strings do not count.
    text = payload.decode('utf-8')
    depth = 0
    quoted = escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in '[{':
            depth += 1
            if depth > MAX_JSON_DEPTH:
                raise ValueError('Too deep')
        elif char in ']}':
            depth -= 1
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate field')
            result[key] = value
        return result
    def finite(value):
        raise ValueError('Nonfinite number')
    def finite_float(text):
        value = float(text)
        if not math.isfinite(value):
            raise ValueError('Nonfinite number')
        return value
    value = json.loads(text, object_pairs_hook=unique, parse_constant=finite, parse_float=finite_float)
    if not isinstance(value, dict):
        raise ValueError('Object required')
    return value


def required_replace(page, old, new):
    if old not in page:
        raise ValueError('Hosted interface template changed; review its copy before serving.')
    return page.replace(old, new)


def entry_style():
    return '<style>body{font:18px system-ui;max-width:760px;margin:3vh auto;padding:24px;line-height:1.6;color:#2a2a2a;background:#fafaf7}h1{color:#143e5a;line-height:1.2}a{color:#143e5a}button,summary{font:inherit;cursor:pointer}button,.start{display:inline-block;padding:14px 22px;background:#143e5a;color:white;border:0;border-radius:7px;font-weight:600}button:disabled{opacity:.6}details{border:1px solid #ccc;padding:12px 18px;border-radius:7px;margin:20px 0}summary{font-weight:600}:focus-visible{outline:3px solid #0094bc;outline-offset:3px}.notice{border-left:4px solid #0094bc;padding:10px 16px;background:#edf6f8}#status{font-weight:600}small{font-size:15px}.callout{border-left:6px solid #143e5a;background:white;padding:4px 20px 8px;margin:20px 0;border-radius:0 7px 7px 0}.callout h2{color:#143e5a;font-size:1.15em;margin:12px 0 4px}.limits{margin-top:28px}</style>'


def recovery_page():
    return ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Start a new illustrative visit</title>'+entry_style()+'<main><h1>Start a new illustrative visit</h1><p>This visit is unavailable in this tab or has expired. Return to the entry page to begin again.</p><p>Server work is temporary. Files already downloaded remain on your device.</p><a class="start" href="/">Return to the start</a></main></html>').encode()


def landing(max_sessions=MAX_SESSIONS, max_starts=24):
    return ('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Try the LIC-DSF scenario tool</title>'''+entry_style()+'''<main><h1>Try the LIC-DSF scenario tool</h1><section class="callout"><h2>What this site is</h2><p>An illustrative walkthrough of the LIC-DSF Scenario Tool. The real tool runs locally on your own computer, so ministries never need to share private data. This site shows the general workflow and collects design feedback: <a href="mailto:lte@tealinsights.com?subject=LIC-DSF%20walkthrough%20feedback">Send design feedback</a>.</p></section><p><strong>Illustrative example.</strong> Not an IMF or World Bank product. Do not enter confidential information. Your visit expires after one hour.</p><p>The example uses the joint IMF and World Bank LIC-DSF template, published by the World Bank, with its built-in illustrative values. It does not represent any actual country. In real use, an analyst starts from their own finished baseline DSA.</p><button id="begin">Start an illustrative visit</button><p id="status" role="status"></p><details class="limits"><summary>Limits and privacy</summary><p>Explore alternative macroeconomic assumptions, compare debt outcomes and prepare a briefing with charts and data. Try the official illustrative workbook and ready-made teaching cases before downloading the app.</p><div class="notice"><strong>Early experimental preview.</strong> Developed iteratively with stakeholder co-design. Not an official IMF or World Bank product.</div><p>''' + DISCLOSURE + '''</p><p>Each visit has a separate temporary workspace on this server. Operators can access server data. Do not enter confidential information or private notes.</p></details><details><summary>Service limits and how calculations work</summary><p>This pilot admits at most MAX_VISITS simultaneous visits and MAX_STARTS new visits per hour. Each visit permits eight calculations, 60 saved edits and 30 completed exports. A chart pair uses two slots; the final slot is reserved for a complete briefing packet.</p><p>One new calculation or export runs at a time. Charts and packets wait automatically in a queue, with one outstanding export per visit. Waiting stops after ten minutes; ready downloads expire after one minute. You can cancel. Changed inputs usually take one to two minutes and may require retry when busy.</p><p>Exact prepared teaching inputs may reuse results calculated at service startup; the evidence identifies reuse. Changed numerical inputs run the calculator. There are no accounts or retained history.</p></details><p><a href="https://github.com/Teal-Insights/lic-dsf-scenario-tool/releases/tag/v0.1.0-alpha.2">Download the local app for your own workbook</a></p></main><script>if(new URLSearchParams(location.search).get('deleted')==='1')document.getElementById('status').textContent='Your visit was deleted. You can start a new illustrative visit.';document.getElementById('begin').onclick=async()=>{const b=document.getElementById('begin'),s=document.getElementById('status');b.disabled=true;s.textContent='Starting your illustrative visit…';try{const r=await fetch('/api/session',{method:'POST',headers:{'Content-Type':'application/json'},body:'{"accept":true}'});if(r.ok)location.href='/app';else s.textContent=(await r.json()).error;}catch{s.textContent='The service could not be reached. Please try again.';}finally{b.disabled=false;}};</script></html>''').replace('MAX_VISITS',str(max_sessions)).replace('MAX_STARTS',str(max_starts)).encode()


def hosted_page():
    page = (Path(__file__).parent / 'web.html').read_text()
    # Keep inert IDs needed by shared wiring; local controls cannot accept input.
    page = required_replace(page, '<div class="row"><div class="field"><label for="file">', '<div class="row" hidden inert><div class="field"><label for="file">')
    page = required_replace(page, '<details><summary>Private reasoning journal</summary>', '<details id="privateJournal" hidden inert><summary>Private reasoning journal</summary>')
    page = required_replace(page, '<textarea id="reasoning"', '<fieldset disabled><textarea disabled id="reasoning"')
    page = required_replace(page, '<button id="saveReasoning">', '<button disabled id="saveReasoning">')
    page = required_replace(page, '<div id="reasoningHistory" class="small"></div></details>', '<div id="reasoningHistory" class="small"></div></fieldset></details>')
    page = required_replace(page, '<body>', '<body><aside class="card"><strong>Illustrative online visit</strong><p class="notice"><strong>Illustrative walkthrough.</strong> The real tool runs locally on your own computer, so ministries never need to share private data. <a href="mailto:lte@tealinsights.com?subject=LIC-DSF%20walkthrough%20feedback">Send design feedback</a>.</p><p>' + DISCLOSURE + '</p><p>When prepared teaching results are enabled, exact teaching inputs reuse results calculated at service startup. They are not freshly calculated for this visit; the result evidence records reuse. Changed numerical inputs run the calculator. Chart and packet rendering run one at a time; the interface waits automatically and lets you cancel.</p><p>Each chart pair uses two of the 30 chart/download slots. The final slot is reserved for Download briefing packet. Charts and packets wait automatically in a bounded queue. You can cancel the wait; saved scenarios are retained.</p><button id="deleteVisit">Delete this visit and return to entry</button><div id="exportWaitPanel" class="hidden"><p id="exportWaitStatus" role="status" aria-live="polite"></p><button id="cancelQueuedExport" type="button">Cancel waiting export</button></div></aside>')
    page = required_replace(page, '</head>', '<style>#exportWaitPanel{position:fixed;bottom:16px;left:50%;transform:translateX(-50%);width:min(600px,calc(100% - 32px));padding:12px 16px;border:1px solid var(--line);border-radius:8px;background:var(--pale);box-shadow:0 4px 18px #0002;z-index:20}#exportWaitStatus{margin:0 0 8px}#upload .row:has(#file),#file,#uploadButton,#privateJournal{display:none!important}</style></head>')
    page = required_replace(page, 'Scenarios are saved separately on this computer.', 'Online scenarios are stored temporarily on the server for this visit.')
    page = required_replace(page, 'Start by uploading your workbook or trying the illustrative example.', 'Start with the official illustrative example.')
    page = required_replace(page, '</body>', '''<script>document.getElementById('deleteVisit').onclick=deleteHostedVisit;document.querySelector('#upload h2').textContent='1. Start the official illustrative example';document.querySelector('#upload .row').hidden=true;</script></body>''')
    page = required_replace(page, 'This is a local, deterministic calculation tool.', 'This is a deterministic calculation tool.')
    page = required_replace(page, 'calculations then run locally.', 'this online mode calculates on the server.')
    page = required_replace(page, 'Workbooks and scenario revisions stay in this local workspace', 'Illustrative scenario revisions are processed and temporarily stored on this server')
    page = required_replace(page, 'Journal entries are retained locally as revisions. They are excluded from shared exports.', 'Private journals are unavailable online. Use the local application for private notes.')
    page = required_replace(page, 'Keep private notes in the private journal.', 'Do not enter private notes online.')
    page = required_replace(page, 'Bring prepared assumptions into an editable draft, or share a saved case with someone using the exact same workbook.', 'Import only illustrative assumptions for this exact example. Import is read in your browser; saving sends its inputs, label and explanations to the server.')
    page = required_replace(page, 'Choose your completed copy of the supported', 'This online experiment uses only the exact official illustrative')
    page = required_replace(page, 'Choose your completed workbook or try the illustrative example.', 'Start the official illustrative example.')
    page = required_replace(page, 'Choose the official illustrative example or upload a supported workbook in step 1 to begin.', 'Start the official illustrative example to begin.')
    page = required_replace(page, '<span>1 Upload</span>', '<span>1 Start example</span>')
    page = required_replace(page, 'Local workspace', 'Temporary server workspace')
    page = required_replace(page, '<div id="caseList"', '<details class="help"><summary>Why can Reference baseline and No investment differ?</summary><p>The official illustrative workbook already uses different domestic-debt paths in its baseline and customized calculations. No investment follows the customized starting point. Compare investment cases with No investment; the pre-existing gap from Reference baseline is not an investment benefit. This reconciles values saved in the sample, not a fresh Excel recalculation.</p></details><div id="caseList"')
    page = required_replace(page, 'First use downloads the official example from the World Bank. After loading it, this copy works offline. No workbook is uploaded to us. If the download fails, check your internet connection and try again, or choose a separately downloaded official workbook.', 'This visit uses the exact official illustrative workbook already configured on the server. No download or local cache is needed. Calculations and saved work stay on the server until this visit ends.')
    page = required_replace(page, 'Try the official illustrative example or upload your completed workbook to get started.', 'Start the official illustrative example to get started.')
    page = required_replace(page, 'Go to upload', 'Start example')
    page = required_replace(page, 'Upload the exact original workbook used to create it; do not rename or edit the file fingerprint.', 'Use the local app for that workbook, or import assumptions for this exact illustrative example; do not edit the file fingerprint.')
    page = required_replace(page, 'your uploaded workbook', 'the official illustrative workbook')
    page = required_replace(page, 'you do not need to upload it again', 'its illustrative scenarios stay available until this visit expires')
    page = required_replace(page, ' Edit the heading or the shared explanations, apply, then refresh both views.', ' Your saved comparison is retained. If the preview quota is reached, download the complete briefing packet; if busy, retry shortly.')
    page = required_replace(page,
        "const blobs=await Promise.all(['standard','briefing'].map(async view=>{const response=await request('/api/export',{...data,view,format:'svg',metric:$('chartMetric').value},true);return await response.blob();}));",
        "const blobs=[];for(const view of ['standard','briefing']){const response=await request('/api/export',{...data,view,format:'svg',metric:$('chartMetric').value},true);blobs.push(await response.blob());}")
    page = required_replace(page, 'Calculating… this usually takes about half a minute. You can keep editing; a newer draft will need its own calculation.', 'Preparing results… exact teaching cases may reuse startup results; changed inputs usually take one to two minutes. You can keep editing.')
    page = required_replace(page, 'Calculating your saved scenario. The next step will show both chart views.', 'Preparing your saved scenario results. The next step will show both chart views; if rendering is busy, retry shortly.')
    page = required_replace(page, '</body>', '<script>' + (Path(__file__).parent / 'hosted_wait.js').read_text() + '</script></body>')
    return page.encode()


def create_app():
    return HostedApplication(os.environ['DSF_DATA_DIR'], os.environ['DSF_OFFICIAL_WORKBOOK'], os.environ['DSF_ORIGIN'], prepare_teaching=os.environ.get('DSF_PREPARED_CACHE', '1') == '1', workshop_test=os.environ.get('DSF_WORKSHOP_TEST', '0') == '1')
