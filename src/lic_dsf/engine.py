"""Serialized evaluation through the generated LIC-DSF library."""
from __future__ import annotations

import hashlib
from importlib.metadata import version, distribution
import json
import math
import os
from pathlib import Path
import platform
import tempfile
import threading
from datetime import datetime, timezone

from .contracts import CONTRACT_VERSION
from .ida21 import PUBLIC, EXTERNAL, DELTA_ROWS, TERMS, METRICS, OFFSETS, probes, cell
from .compare import compare_one
from .workbooks import inspect_workbook, file_hash, IntakeError
from .workbook_cells import apply_number_cells
from .scenarios import normalize_scenario

LIBRARY_DISTRIBUTION = "lic-dsf-2025-08-12"
ENGINE_VERSION = "0.1.0"
ENGINE_REVISION = "722504c5caac3d8318dc46ee0fbb9ff568b87c18"
_A2 = "A2. Alternative Scenario :[Customize, enter title]"
# attribute, scenario key for the reference baseline, attribute, scenario key for customized
_SERIES = {
    "ext_pv_gdp": ("chart_output_pv_debt_gdp_ratio", "Baseline", "chart_pv_debt_gdp_ratio_custom_alternative_scenario", None),
    "ext_pv_exports": ("chart_output_pv_debt_to_exports", "Baseline", "chart_pv_debt_to_exports_custom_alternative_scenario", None),
    "ext_ds_exports": ("chart_output_debt_service_to_exports", "Baseline", "chart_debt_service_to_exports_custom_alternative_scenario", None),
    "ext_ds_revenue": ("chart_output_debt_service_to_revenue", "Baseline", "chart_debt_service_to_revenue_custom_alternative_scenario", None),
    "public_pv_gdp": ("chart_output_chart_data_pv_of_debt_to_gdp_ratio_pv_debt_to_gdp", "Baseline", "chart_output_chart_data_pv_of_debt_to_gdp_ratio_pv_debt_to_gdp", _A2),
    "public_pv_revenue": ("chart_output_chart_data_pv_of_debt_to_revenue_ratio_pv_debt_to_revenue", "Baseline", "chart_output_chart_data_pv_of_debt_to_revenue_ratio_pv_debt_to_revenue", _A2),
}
_SENTINELS = {
    "external_rating": "external_dsa_risk_rating_signal",
    "overall_rating": "overall_risk_rating_signal",
    "external_signal": "external_dsa_risk_rating_signal",
    "selected_shock": "external_pv_debt_to_gdp_mx_shock",
}
_LOCK = threading.RLock()
_CACHE = {}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def engine_identity():
    versions = {name: version(name) for name in (LIBRARY_DISTRIBUTION, 'fastpyxl', 'numpy', 'openpyxl', 'PyYAML')}
    if versions[LIBRARY_DISTRIBUTION] != ENGINE_VERSION:
        raise IntakeError('unsupported_engine_version')
    direct = distribution(LIBRARY_DISTRIBUTION).read_text('direct_url.json')
    recorded_revision = json.loads(direct).get('vcs_info', {}).get('commit_id') if direct else None
    if recorded_revision != ENGINE_REVISION:
        raise IntakeError('engine_source_revision_unverified')
    package = Path(__file__).parent
    code = {p.name: file_hash(p) for p in sorted(package.glob('*.py'))}
    return {'python': platform.python_version(), 'implementation': platform.python_implementation(),
            'platform': platform.system(), 'machine': platform.machine(), 'versions': versions,
            'engine_revision': ENGINE_REVISION, 'core_sha256': digest(code),
            'contract_version': CONTRACT_VERSION, 'dynamic_references': 'generated_library_chart_series'}


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


def load_model(path):
    """Bind workbook input cells through the generated library."""
    from lic_dsf_2025_08_12 import Model
    return Model.from_workbook(path)


def _at(series, year, scenario):
    # The workbook's projection year, not the library snapshot's 2024 column.
    if scenario is None:
        return series.sel(TIME_PERIOD=year)
    return series.sel(SCENARIO=scenario, TIME_PERIOD=year)


def _sample(model, first_projection_year):
    result = {}
    for metric, _title, _units, _sheet, _base, _custom, _col, _header in METRICS:
        baseline_attr, baseline_scenario, custom_attr, custom_scenario = _SERIES[metric]
        baseline = getattr(model, baseline_attr)
        custom = getattr(model, custom_attr)
        for offset in OFFSETS:
            year = first_projection_year + offset
            result[f'{metric}:{offset}:reference_baseline'] = _plain(_at(baseline, year, baseline_scenario))
            result[f'{metric}:{offset}:customized'] = _plain(_at(custom, year, custom_scenario))
    for name, attr in _SENTINELS.items():
        result[f'sentinel:{name}'] = _plain(getattr(model, attr))
    return result


def _scenario_edits(definition):
    public = {}
    for row in DELTA_ROWS:
        for offset, value in enumerate(definition['delta_paths'][str(row)]):
            public[cell(5 + offset, row)] = value
    edits = {PUBLIC: public}
    terms = definition['terms']
    if terms:
        edits[EXTERNAL] = {TERMS[key]: value for key, value in terms.items()}
    return edits


def _scenario_workbook(path, definition):
    handle, name = tempfile.mkstemp(suffix='.xlsm')
    os.close(handle)
    apply_number_cells(path, name, _scenario_edits(definition))
    return name


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
    scenario_path = None
    with _LOCK:
        model = _CACHE.get(key)
        if model is None:
            model = load_model(path)
            _CACHE[key] = model
            while len(_CACHE) > 2:
                del _CACHE[next(iter(_CACHE))]
        try:
            supplied = _sample(model, info['first_projection_year'])
            if definition is not None:
                scenario_path = _scenario_workbook(path, definition)
                computed = _sample(load_model(scenario_path), info['first_projection_year'])
            else:
                computed = dict(supplied)
        finally:
            if scenario_path is not None:
                Path(scenario_path).unlink(missing_ok=True)
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
    for metric, _title, units, sheet, base, custom, col, _header in METRICS:
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
