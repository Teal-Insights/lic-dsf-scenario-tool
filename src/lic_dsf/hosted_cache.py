"""Immutable, startup-only public teaching results; never visitor state."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import MappingProxyType
from .engine import digest, engine_identity
from .contracts import CONTRACT_VERSION
from .illustrative import builtin_investment_cases, OFFICIAL_SHA256, OFFICIAL_YEARS
from .scenarios import normalize_scenario

REUSE_WARNING = 'prepared_teaching_result_reused_not_recalculated_for_this_visit'


def canonical_definitions():
    return [normalize_scenario(c['scenario_file']['definition'], list(OFFICIAL_YEARS))
            for c in builtin_investment_cases(OFFICIAL_SHA256, list(OFFICIAL_YEARS))]


class PreparedCache:
    def __init__(self, results, identity):
        definitions = {digest(d): d for d in canonical_definitions()}
        admitted = {}
        for result in results:
            key = result.get('scenario_hash')
            raw = dict(result); run_hash = raw.pop('run_hash', None)
            expected_fields = {'contract_version','workbook_sha256','first_projection_year','input_years','engine_identity','scenario','scenario_hash','points','thresholds','evidence','warnings','created_utc','run_hash'}
            if (set(result) != expected_fields or len(result.get('points', [])) != 36 or key not in definitions or key in admitted or result.get('scenario') != definitions[key]
                    or result.get('workbook_sha256') != OFFICIAL_SHA256
                    or result.get('engine_identity') != identity
                    or result.get('contract_version') != CONTRACT_VERSION
                    or result.get('input_years') != list(OFFICIAL_YEARS)
                    or result.get('evidence', {}).get('calculation') != 'computed_unverified'
                    or run_hash != digest(raw)):
                raise ValueError('Prepared teaching result failed its exact identity/integrity check.')
            admitted[key] = json.dumps(result, sort_keys=True, allow_nan=False)
        if len(admitted) != 3:
            raise ValueError('All three exact prepared teaching results are required.')
        self._results = MappingProxyType(admitted)  # immutable serialized values; fresh decoded copy per use
        self._identity = json.dumps(identity, sort_keys=True, allow_nan=False)

    def lookup(self, workbook_sha, definition):
        if workbook_sha != OFFICIAL_SHA256 or json.dumps(engine_identity(), sort_keys=True) != self._identity:
            return None
        encoded = self._results.get(digest(definition))
        if encoded is None:
            return None
        result = json.loads(encoded)
        if result['scenario'] != definition:
            return None
        source_hash = result.pop('run_hash')
        result['evidence']['execution'] = {
            'mode': 'prepared_teaching_result_reused',
            'fresh_calculation_for_visit': False,
            'prepared_utc': result['created_utc'],
            'prepared_result_hash': source_hash,
        }
        result['warnings'] = sorted(set(result['warnings']) | {REUSE_WARNING})
        result['run_hash'] = digest(result)
        return result


def prepare(workbook, root):
    """Run three bounded children before serving traffic; discard all scratch on exit."""
    workbook = Path(workbook)
    if hashlib.sha256(workbook.read_bytes()).hexdigest() != OFFICIAL_SHA256:
        raise ValueError('Prepared workbook identity does not match.')
    identity = engine_identity()
    results = []
    for definition in canonical_definitions():
        with tempfile.TemporaryDirectory(prefix='prepared-', dir=root) as temporary:
            directory = Path(temporary)
            request = directory / 'request.json'
            request.write_text(json.dumps({'workbook': str(workbook), 'workbook_sha256': OFFICIAL_SHA256,
                'scenario': definition, 'parent_pid': os.getpid(), 'deadline_utc': time.time() + 180}, allow_nan=False))
            child = subprocess.Popen([sys.executable, '-B', '-m', 'lic_dsf.hosted_worker', str(request)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            try:
                child.wait(timeout=180)
            except BaseException:
                child.kill(); child.wait(timeout=5)
                raise
            if child.returncode:
                raise ValueError('Prepared teaching warm-up failed within service limits.')
            result = directory / 'result.json'
            if result.stat().st_size > 16 * 1024 * 1024:
                raise ValueError('Prepared result exceeds the service limit.')
            results.append(json.loads(result.read_text()))
    if identity != engine_identity():
        raise ValueError('Calculation runtime changed during preparation.')
    return PreparedCache(results, identity)
