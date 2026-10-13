"""Synthetic hosted result-boundary controls; no workbook or calculator runs.

Official teaching definitions are public source data. The child result payloads
below are independently authored neutral fixtures, not numerical acceptance.
Only child/process scheduling is substituted; real store, cache and export
field selection enforce the unchanged identities and stale-result gates.
"""
import copy
from concurrent.futures import Future
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from lic_dsf.app import shareable
from lic_dsf.briefing_pack import tables
from lic_dsf.contracts import CONTRACT_VERSION
from lic_dsf.hosted import HostedWorkspace, OFFICIAL_EXAMPLE_SHA
from lic_dsf.hosted_cache import PreparedCache, canonical_definitions, REUSE_WARNING
from lic_dsf.ida21 import METRICS, OFFSETS, cell
from lic_dsf.illustrative import OFFICIAL_YEARS
from lic_dsf.store import ScenarioStore, StaleResult, canonical


IDENTITY = {'synthetic_execution_boundary_control': True,
            'contract_version': CONTRACT_VERSION}


def literal_digest(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False,
                         separators=(',', ':'), allow_nan=False).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def fixture_result(definition):
    points = []
    for metric, title, units, sheet, base, custom, column, header in METRICS:
        for offset in OFFSETS:
            points.append({'metric': metric, 'year': OFFICIAL_YEARS[0] + offset,
                'units': units, 'reference_baseline': 0.0,
                'as_supplied_customized': 0.0, 'scenario': -0.0,
                'source_cells': {'reference_baseline': f'{sheet}!{cell(column + offset, base)}',
                                 'customized': f'{sheet}!{cell(column + offset, custom)}'}})
    result = {'contract_version': CONTRACT_VERSION,
              'workbook_sha256': OFFICIAL_EXAMPLE_SHA,
              'first_projection_year': OFFICIAL_YEARS[0],
              'input_years': list(OFFICIAL_YEARS),
              'engine_identity': copy.deepcopy(IDENTITY),
              'scenario': copy.deepcopy(definition),
              'scenario_hash': literal_digest(definition),
              'points': points, 'thresholds': {},
              'evidence': {'calculation': 'computed_unverified',
                           'exact_excel': 'pending', 'structural': 'passed'},
              'warnings': ['exact_excel_comparison_pending'],
              'created_utc': '2026-01-01T00:00:00+00:00'}
    result['run_hash'] = literal_digest(result)
    return result


class HeldExecutor:
    """Explicitly release an unchanged callback; never start a thread."""
    def __init__(self):
        self.callback = self.future = None

    def submit(self, callback):
        self.callback = callback
        self.future = Future()
        return self.future

    def run(self):
        if self.future.set_running_or_notify_cancel():
            self.callback()
            self.future.set_result(None)


@contextmanager
def workspace(prepared_cache=None, *, canonical_case=False):
    with tempfile.TemporaryDirectory() as root:
        directory = Path(root) / 'visit'
        directory.mkdir()
        store = ScenarioStore(directory / 'store')
        store.register_workbook(OFFICIAL_EXAMPLE_SHA, 'Official illustrative example')
        definition = canonical_definitions()[0]
        if not canonical_case:
            # A public teaching-definition rate edit is an actual cache miss.
            definition['terms']['rate'] += .001
        saved = store.save_scenario(OFFICIAL_EXAMPLE_SHA, 'Public boundary control',
                                   definition, share_label='Public boundary control')
        ws = HostedWorkspace.__new__(HostedWorkspace)
        ws.owner = SimpleNamespace(compute=threading.BoundedSemaphore(1),
            lock=threading.RLock(), prepared_cache=prepared_cache,
            workbook=Path(root) / 'public-example-not-opened.xlsm')
        ws.store, ws.directory, ws.executor = store, directory, HeldExecutor()
        ws.jobs, ws.child, ws.closed = {}, None, False
        yield ws, saved


def run_child_boundary(ws, saved, payload, *, mode='success', after_wait=None):
    """Supply a neutral child file through the genuine result/read/store path."""
    observed = {'popen': 0, 'wait': 0, 'kill': 0, 'requests': []}

    class Child:
        def __init__(self, request):
            self.request, self.returncode = request, None

        def wait(self, *, timeout):
            observed['wait'] += 1
            if mode == 'timeout' and observed['wait'] == 1:
                raise subprocess.TimeoutExpired('synthetic hosted child', timeout)
            if self.returncode == -9:
                return self.returncode
            self.returncode = 1 if mode == 'nonzero' else 0
            if mode not in ('nonzero', 'missing'):
                target = self.request.parent / 'result.json'
                target.write_text('invalid JSON' if mode == 'malformed' else canonical(payload),
                                  encoding='utf-8')
            if after_wait is not None:
                after_wait()
            return self.returncode

        def kill(self):
            observed['kill'] += 1
            self.returncode = -9

    def popen(command, **kwargs):
        observed['popen'] += 1
        assert command[-2] == 'lic_dsf.hosted_worker'
        assert kwargs['start_new_session'] is True
        request = Path(command[-1])
        observed['requests'].append(json.loads(request.read_text()))
        return Child(request)

    started = ws.start_calculation(saved['id'])
    with patch('lic_dsf.hosted.subprocess.Popen', side_effect=popen):
        ws.executor.run()
    return started['job_id'], observed


def stored_run(ws, saved):
    return ws.store.current_run(saved['id'], engine_identity=IDENTITY,
                                contract_version=CONTRACT_VERSION)


def run_count(ws):
    with ws.store._connection() as db:
        return db.execute('SELECT COUNT(*) FROM runs').fetchone()[0]


class HostedExecutionEvidenceTests(unittest.TestCase):
    def test_01_successful_uncached_child_preserves_all_data_and_binds_new_hash(self):
        with workspace() as (ws, saved):
            payload = fixture_result(saved['definition'])
            original = copy.deepcopy(payload)
            expected_execution = {'mode': 'fresh_calculation_for_visit',
                'fresh_calculation_for_visit': True,
                'calculated_result_hash': original['run_hash']}
            job_id, observed = run_child_boundary(ws, saved, payload)
            actual = stored_run(ws, saved)
            result = actual['result']
            self.assertEqual(ws.jobs[job_id]['status'], 'complete')
            self.assertEqual((observed['popen'], observed['wait'], observed['kill']), (1, 1, 0))
            self.assertEqual(observed['requests'][0]['scenario'], saved['definition'])
            self.assertEqual(result['evidence']['execution'], expected_execution)
            restored = copy.deepcopy(result)
            restored['evidence'].pop('execution')
            restored['run_hash'] = original['run_hash']
            self.assertEqual(canonical(restored), canonical(original))
            unhashed = copy.deepcopy(result)
            result_hash = unhashed.pop('run_hash')
            self.assertEqual(result_hash, literal_digest(unhashed))
            self.assertNotEqual(result_hash, original['run_hash'])
            self.assertEqual(actual['result_hash'], literal_digest(result))
            self.assertEqual(ws.jobs[job_id]['evidence'], result['evidence'])
            self.assertEqual(payload, original)
            self.assertFalse((ws.directory / 'jobs' / job_id).exists())
            self.assertTrue(ws.owner.compute.acquire(blocking=False))
            ws.owner.compute.release()

    def test_02_real_prepared_cache_keeps_false_and_never_starts_child(self):
        results = [fixture_result(definition) for definition in canonical_definitions()]
        original = copy.deepcopy(results[0])
        cache = PreparedCache(results, IDENTITY)
        with workspace(cache, canonical_case=True) as (ws, saved):
            with patch('lic_dsf.hosted_cache.engine_identity', return_value=IDENTITY), \
                 patch('lic_dsf.hosted.subprocess.Popen', side_effect=AssertionError('cache must not spawn')) as popen:
                job_id = ws.start_calculation(saved['id'])['job_id']
            result = stored_run(ws, saved)['result']
            execution = result['evidence']['execution']
            self.assertEqual(execution['mode'], 'prepared_teaching_result_reused')
            self.assertIs(execution['fresh_calculation_for_visit'], False)
            self.assertEqual(execution['prepared_result_hash'], original['run_hash'])
            self.assertNotIn('calculated_result_hash', execution)
            self.assertIn(REUSE_WARNING, result['warnings'])
            self.assertEqual(canonical(result['points']), canonical(original['points']))
            raw = copy.deepcopy(result)
            self.assertEqual(raw.pop('run_hash'), literal_digest(raw))
            self.assertEqual(ws.jobs[job_id]['status'], 'complete')
            self.assertIsNone(ws.executor.callback)
            popen.assert_not_called()

    def test_03_failed_missing_and_malformed_results_never_record_fresh_run(self):
        for mode in ('nonzero', 'missing', 'malformed', 'timeout'):
            with self.subTest(mode=mode), workspace() as (ws, saved):
                before = ws.store.get_scenario(saved['id'])
                job_id, observed = run_child_boundary(ws, saved, fixture_result(saved['definition']), mode=mode)
                self.assertEqual(ws.jobs[job_id]['status'], 'failed')
                self.assertNotIn('evidence', ws.jobs[job_id])
                self.assertEqual(run_count(ws), 0)
                with self.assertRaises(StaleResult):
                    stored_run(ws, saved)
                self.assertEqual(ws.store.get_scenario(saved['id']), before)
                self.assertFalse((ws.directory / 'jobs' / job_id).exists())
                self.assertEqual(observed['kill'], int(mode == 'timeout'))
                self.assertTrue(ws.owner.compute.acquire(blocking=False))
                ws.owner.compute.release()

    def test_04_real_revision_and_result_identity_gates_refuse_stale_output(self):
        for mode in ('revision', 'definition', 'workbook', 'scenario_hash'):
            with self.subTest(mode=mode), workspace() as (ws, saved):
                payload = fixture_result(saved['definition'])
                edit = copy.deepcopy(saved['definition'])
                edit['terms']['rate'] += .001
                after_wait = None
                if mode == 'revision':
                    after_wait = lambda: ws.store.save_scenario(OFFICIAL_EXAMPLE_SHA,
                        'Public edited control', edit, scenario_id=saved['id'],
                        expected_revision=saved['revision'], share_label='Public boundary control')
                elif mode == 'definition':
                    payload['scenario'] = edit
                    payload['scenario_hash'] = literal_digest(edit)
                elif mode == 'workbook':
                    payload['workbook_sha256'] = 'f' * 64
                else:
                    payload['scenario_hash'] = 'f' * 64
                payload.pop('run_hash')
                payload['run_hash'] = literal_digest(payload)
                job_id, observed = run_child_boundary(ws, saved, payload, after_wait=after_wait)
                self.assertEqual(ws.jobs[job_id]['status'], 'failed')
                self.assertNotIn('evidence', ws.jobs[job_id])
                self.assertEqual(run_count(ws), 0)
                current = ws.store.get_scenario(saved['id'])
                self.assertEqual(current['revision'], 2 if mode == 'revision' else 1)
                self.assertEqual(current['definition'], edit if mode == 'revision' else saved['definition'])
                self.assertEqual(observed['popen'], 1)

    def test_05_cancelled_queued_or_closed_visit_never_records_execution(self):
        with workspace() as (ws, saved):
            job_id = ws.start_calculation(saved['id'])['job_id']
            with patch('lic_dsf.hosted.subprocess.Popen') as popen:
                self.assertTrue(ws.executor.future.cancel())
                ws.executor.run()
            popen.assert_not_called()
            self.assertEqual(run_count(ws), 0)
            self.assertNotIn('evidence', ws.jobs[job_id])
            self.assertTrue(ws.owner.compute.acquire(blocking=False))
            ws.owner.compute.release()
        with workspace() as (ws, saved):
            job_id, observed = run_child_boundary(ws, saved, fixture_result(saved['definition']),
                                                 after_wait=lambda: setattr(ws, 'closed', True))
            self.assertEqual(observed['popen'], 1)
            self.assertEqual(run_count(ws), 0)
            self.assertNotIn('evidence', ws.jobs[job_id])
            self.assertTrue(ws.owner.compute.acquire(blocking=False))
            ws.owner.compute.release()

    def test_06_real_store_json_and_packet_evidence_preserve_execution(self):
        with workspace() as (ws, saved):
            payload = fixture_result(saved['definition'])
            run_child_boundary(ws, saved, payload)
            comparison = ws.store.comparison([saved['id']], saved['id'],
                engine_identity=IDENTITY, contract_version=CONTRACT_VERSION,
                workbook_sha=OFFICIAL_EXAMPLE_SHA, expected_chart_context_revision=0)
            public = shareable(comparison)
            result = public['runs'][0]['result']
            self.assertIs(result['evidence']['execution']['fresh_calculation_for_visit'], True)
            self.assertEqual(result['evidence']['exact_excel'], 'pending')
            self.assertEqual(canonical(result['points']), canonical(payload['points']))
            self.assertNotIn('name', public['runs'][0])
            self.assertNotIn('workbook', public)
            evidence_rows = tables(public)['Evidence']
            evidence_column = evidence_rows[0].index('evidence_json')
            self.assertEqual(json.loads(evidence_rows[1][evidence_column]), result['evidence'])
            self.assertEqual(evidence_rows[1][2], public['runs'][0]['result_hash'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
