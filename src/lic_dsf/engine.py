"""Serialized, reversible evaluation over an immutable workbook identity."""
from __future__ import annotations

import hashlib
from importlib.metadata import version, distribution
import json
import math
from pathlib import Path
import platform
import threading
from datetime import datetime, timezone

from .contracts import CONTRACT_VERSION
from .ida21 import PUBLIC, EXTERNAL, DELTA_ROWS, TERMS, METRICS, OFFSETS, probes, cell
from .compare import compare_one
from .workbooks import inspect_workbook, file_hash, IntakeError
from .scenarios import normalize_scenario

ENGINE_VERSION = '3.7.0'
ENGINE_REVISION = '15c51591b73b1dfb97088d46c6c0741bc59769b4'
_LOCK = threading.RLock()
_CACHE = {}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def engine_identity():
    versions = {name: version(name) for name in ('excel-grapher', 'fastpyxl', 'numpy', 'openpyxl', 'PyYAML')}
    if versions['excel-grapher'] != ENGINE_VERSION:
        raise IntakeError('unsupported_engine_version')
    direct = distribution('excel-grapher').read_text('direct_url.json')
    recorded_revision = json.loads(direct).get('vcs_info', {}).get('commit_id') if direct else None
    if recorded_revision != ENGINE_REVISION:
        raise IntakeError('engine_source_revision_unverified')
    package = Path(__file__).parent
    code = {p.name: file_hash(p) for p in sorted(package.glob('*.py'))}
    return {'python': platform.python_version(), 'implementation': platform.python_implementation(),
            'platform': platform.system(), 'machine': platform.machine(), 'versions': versions,
            'engine_revision': ENGINE_REVISION, 'core_sha256': digest(code),
            'contract_version': CONTRACT_VERSION, 'dynamic_references': 'cached_geometry_with_sentinel_checks'}


def _plain(value):
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise IntakeError('nonfinite_engine_output')
        return value
    if hasattr(value, 'item'):
        return _plain(value.item())
    raise IntakeError('unsupported_engine_output_type')


class _Graph:
    def __init__(self, path):
        from excel_grapher import create_dependency_graph
        from .excel_semantics import apply
        apply()
        self.probes = probes()
        targets = [f"{p['sheet']}!{p['cell']}" for p in self.probes]
        targets += [f"'{PUBLIC}'!E10:Y38", f"'{EXTERNAL}'!C21:C24"]
        self.graph = create_dependency_graph(path, targets, load_values=True, use_cached_dynamic_refs=True)
        self.keys = {str(k).upper().replace("'", ''): k for k in self.graph.keys()}
        self.original = {}

    def restore(self):
        for key, (value, formula, normalized) in self.original.items():
            self.graph.set_node_formula(key, formula, normalized)
            self.graph.set_node_value(key, value)
        self.original.clear()

    def apply(self, scenario):
        writes = [(PUBLIC, cell(5 + offset, row), value)
                  for row in DELTA_ROWS for offset, value in enumerate(scenario['delta_paths'][str(row)])]
        writes += [(EXTERNAL, TERMS[key], value) for key, value in (scenario['terms'] or {}).items()]
        keyed = [(self.keys.get(f'{sheet}!{address}'.upper()), value) for sheet, address, value in writes]
        if any(key is None for key, value in keyed):
            raise IntakeError('input_target_missing_from_graph')
        for key, value in keyed:
            node = self.graph.get_node(key)
            if key not in self.original:
                self.original[key] = (node.value, node.formula, node.normalized_formula)
            if node.formula:
                self.graph.set_node_formula(key, None, None)
            self.graph.set_node_value(key, value)

    def evaluate(self):
        from excel_grapher import FormulaEvaluator
        targets = [f"{p['sheet']}!{p['cell']}" for p in self.probes]
        with FormulaEvaluator(self.graph) as evaluator:
            values = evaluator.evaluate(targets)
        normalized = {str(k).upper().replace("'", ''): value for k, value in values.items()}
        result = {}
        for p, target in zip(self.probes, targets):
            key = target.upper().replace("'", '')
            if key not in normalized:
                raise IntakeError('output_probe_missing_from_evaluator')
            result[p['id']] = _plain(normalized[key])
        return result


def calculate(path, scenario=None, expected_sha256=None):
    """Evaluate as supplied or a complete new customized path; never save the workbook."""
    from .scenarios import InputError
    try:
        return _calculate(path, scenario, expected_sha256)
    except (IntakeError, InputError):
        raise
    except Exception as exc:
        raise IntakeError('calculation_failed_private_details_available') from exc


def _calculate(path, scenario=None, expected_sha256=None):
    path = Path(path)
    info = inspect_workbook(path)
    if info['compatibility']['status'] != 'supported':
        raise IntakeError('unsupported_workbook_contract')
    sha = info['workbook_sha256']
    if expected_sha256 is not None and expected_sha256 != sha:
        raise IntakeError('workbook_identity_changed')
    definition = None if scenario is None else normalize_scenario(scenario, info['input_years'])
    identity = engine_identity()
    import openpyxl
    cached = openpyxl.load_workbook(path, read_only=True, data_only=True, keep_links=False)
    try:
        expected = {p['id']: cached[p['sheet']][p['cell']].value for p in probes()}
    finally:
        cached.close()
    key = (sha, digest(identity))
    with _LOCK:
        graph = _CACHE.get(key)
        if graph is None:
            graph = _Graph(path)
            _CACHE[key] = graph
            while len(_CACHE) > 2:
                del _CACHE[next(iter(_CACHE))]
        try:
            graph.restore()
            supplied = graph.evaluate()
            if definition is not None:
                graph.apply(definition)
                computed = graph.evaluate()
            else:
                computed = dict(supplied)
        finally:
            graph.restore()
    if file_hash(path) != sha:
        _CACHE.pop(key, None)
        raise IntakeError('workbook_changed_during_calculation')
    cache_checks = [(p, *compare_one(expected[p], supplied[p])) for p in expected]
    mismatches = [p for p, ok, reason in cache_checks if not ok]
    dynamic = [p for p in supplied if p.startswith('sentinel:') and not compare_one(supplied[p], computed[p])[0]]
    degradation = [p for p in supplied if isinstance(supplied[p], (int, float)) and not isinstance(supplied[p], bool)
                   and (computed[p] is None or isinstance(computed[p], str) and computed[p].startswith('#'))]
    baseline_changed = [p for p in supplied if p.endswith(':reference_baseline') and not compare_one(supplied[p], computed[p])[0]]
    warnings = list(info['warnings']) + ['exact_excel_comparison_pending', 'sampled_years_only', 'public_debt_service_revenue_not_included']
    if dynamic or degradation or baseline_changed:
        warnings.append('dynamic_reference_or_output_change_requires_review')
    evidence = {'structural': 'passed', 'formula_profile': 'not_verified',
                'saved_cache': 'matched' if not mismatches else 'mismatch',
                'cache_passed': len(cache_checks) - len(mismatches), 'cache_total': len(cache_checks),
                'cache_mismatch_probes': mismatches, 'exact_excel': 'pending',
                'dynamic_reference_check': 'review_required' if dynamic or degradation or baseline_changed else 'no_trigger_observed',
                'review_probes': sorted(set(dynamic + degradation + baseline_changed)),
                'calculation': 'review_required' if mismatches or dynamic or degradation or baseline_changed else 'computed_unverified'}
    points = []
    for metric, title, units, sheet, base, custom, col, header in METRICS:
        for offset in OFFSETS:
            points.append({'metric': metric, 'year': info['first_projection_year'] + offset, 'units': units,
                           'reference_baseline': supplied[f'{metric}:{offset}:reference_baseline'],
                           'as_supplied_customized': supplied[f'{metric}:{offset}:customized'],
                           'scenario': computed[f'{metric}:{offset}:customized'],
                           'source_cells': {'reference_baseline': f'{sheet}!{cell(col + offset, base)}',
                                            'customized': f'{sheet}!{cell(col + offset, custom)}'}})
    result = {'contract_version': CONTRACT_VERSION, 'workbook_sha256': sha,
              'first_projection_year': info['first_projection_year'], 'input_years': info['input_years'],
              'engine_identity': identity, 'scenario': definition, 'scenario_hash': digest(definition),
              'points': points, 'thresholds': info['thresholds'], 'evidence': evidence,
              'warnings': sorted(set(warnings)), 'created_utc': datetime.now(timezone.utc).isoformat()}
    result['run_hash'] = digest(result)
    return result
