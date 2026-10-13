"""FIFO export jobs, one outstanding job per visitor and one heavy worker."""
from collections import deque
import threading
import subprocess
import uuid

MAX_QUEUE = 25
JOB_SECONDS = 600
READY_SECONDS = 60
MAX_RESULT = 32 * 1024 * 1024


class ExportQueue:
    def __init__(self, owner):
        self.owner = owner
        self.jobs = {}
        self.by_visitor = {}
        self.waiting = deque()
        self.wake = threading.Event()
        self.stopping = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True, name='bounded-export-queue')
        self.thread.start()

    def has_waiting(self):
        return any(j['status'] in {'queued', 'running'} for j in self.jobs.values())

    def submit(self, ws, comparison, data, request_key):
        self.expire()
        old = self.by_visitor.get(ws)
        if old in self.jobs:
            if self.jobs[old]['status'] in {'queued', 'running'}:
                raise ValueError('This visit already has an export waiting. Wait or cancel it first.')
        ws.check_export_quota(data)
        occupied = sum(j['status'] in {'queued', 'running', 'ready'} for j in self.jobs.values())
        if old in self.jobs and self.jobs[old]['status'] == 'ready':
            occupied -= 1
        if occupied >= MAX_QUEUE:
            return None
        if old in self.jobs:
            self._remove(old)
        key = uuid.uuid4().hex
        self.jobs[key] = {'ws': ws, 'data': data, 'comparison': comparison, 'status': 'queued',
                          'created': self.owner.clock(), 'body': None, 'request_key': request_key}
        self.by_visitor[ws] = key
        self.waiting.append(key)
        self.wake.set()
        return key

    def own(self, ws, key):
        job = self.jobs.get(key)
        return job if job and job['ws'] is ws else None

    def _remove(self, key):
        job = self.jobs.pop(key, None)
        if job and self.by_visitor.get(job['ws']) == key:
            del self.by_visitor[job['ws']]
        if job:
            job.update(body=None, comparison=None, data=None, ws=None)
        try:
            self.waiting.remove(key)
        except ValueError:
            pass

    def cancel(self, ws, key, reason='cancelled'):
        job = self.own(ws, key)
        if not job:
            return False
        was_running = job['status'] == 'running'
        job.update(status=reason, body=None, comparison=None, finished=self.owner.clock())
        if was_running and ws.export_child is not None and ws.export_child.poll() is None:
            ws.export_child.kill()
            ws.export_child.wait(timeout=5)
        try:
            self.waiting.remove(key)
        except ValueError:
            pass
        self.wake.set()
        return True

    def cancel_visitor(self, ws):
        key = self.by_visitor.get(ws)
        if key:
            self.cancel(ws, key)
            self._remove(key)

    def expire(self):
        now = self.owner.clock()
        for key, job in list(self.jobs.items()):
            if job['ws'].closed:
                self.cancel_visitor(job['ws'])
            elif job['status'] in {'queued', 'running', 'ready'} and (
                    now - job['created'] >= JOB_SECONDS or
                    (job['status'] == 'ready' and now - job['finished'] >= READY_SECONDS)):
                self.cancel(job['ws'], key, 'expired')
            elif job['status'] in {'cancelled', 'expired', 'failed'} and now - job['finished'] >= READY_SECONDS:
                self._remove(key)

    def status(self, ws, key):
        job = self.own(ws, key)
        if not job:
            return None
        position = None
        if job['status'] == 'queued':
            position = list(self.waiting).index(key) + 1
        return {'job_id': key, 'request_key': job['request_key'], 'status': job['status'], 'position': position,
                'message': 'Waiting for another visitor’s chart export' if job['status'] == 'queued'
                           else 'Preparing your chart or packet' if job['status'] == 'running'
                           else 'Export ready' if job['status'] == 'ready'
                           else 'Export ended. Your saved scenarios remain available.'}

    def take(self, ws, key):
        job = self.own(ws, key)
        if not job or job['status'] != 'ready':
            return None
        # Safe replay for the ready TTL. A new submission replaces this one body.
        # The successful render already consumed one slot; polls/retrievals do not.
        return job['body']

    def _run(self):
        while not self.stopping.is_set():
            self.wake.wait(.2)
            self.wake.clear()
            with self.owner.lock:
                if self.stopping.is_set():
                    break
                try:
                    self.expire()
                except (OSError, TimeoutError, subprocess.TimeoutExpired):
                    self.owner.cleanup_failed = True
                    continue
                while self.waiting and self.waiting[0] not in self.jobs:
                    self.waiting.popleft()
                if not self.waiting:
                    continue
                # All admission uses the same owner lock. Probe and release while
                # holding it, then bounded_export acquires the permit without a race.
                if not self.owner.compute.acquire(blocking=False):
                    continue
                self.owner.compute.release()
                key = self.waiting.popleft()
                job = self.jobs[key]
                ws = job['ws']
                job['status'] = 'running'
                body = None
                try:
                    body = ws.bounded_export(job['comparison'], job['data'], count_response=False)
                    if len(body[0]) > MAX_RESULT:
                        raise ValueError('Export is too large.')
                    if job['status'] == 'running' and not ws.closed:
                        ws.check_export_quota(job['data'])
                        ws.exports += 1
                        job.update(status='ready', body=body, comparison=None, finished=self.owner.clock())
                except Exception:
                    if job['status'] == 'running':
                        job.update(status='failed', body=None, comparison=None, finished=self.owner.clock())
                job = ws = body = None
                self.wake.set()
