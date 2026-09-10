"""Full-horizon inputs prevent residual shocks from an earlier scenario."""
import math
from .ida21 import DELTA_ROWS


class InputError(ValueError):
    pass


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise InputError("Enter a finite number; a blank is not zero.")
    return float(value)


def normalize_scenario(scenario, years):
    if not isinstance(scenario, dict) or set(scenario) != {"delta_paths", "terms"}:
        raise InputError("Scenario requires delta_paths and terms.")
    paths = scenario['delta_paths']
    if not isinstance(paths, dict) or set(paths) != {str(r) for r in DELTA_ROWS}:
        raise InputError("All 13 customized input paths are required.")
    normalized = {}
    for row in DELTA_ROWS:
        path = paths[str(row)]
        if not isinstance(path, list) or len(path) != len(years):
            raise InputError("Every input must cover the complete supported horizon.")
        normalized[str(row)] = [number(v) for v in path]
    terms = scenario['terms']
    if terms is not None:
        if not isinstance(terms, dict) or set(terms) != {'rate', 'grace_years', 'maturity_years'}:
            raise InputError("Provide all three terms or inherit supplied terms.")
        terms = {key: number(value) for key, value in terms.items()}
        if terms['rate'] < 0 or terms['grace_years'] < 0 or terms['maturity_years'] <= terms['grace_years']:
            raise InputError("Rate and grace cannot be negative; maturity must exceed grace.")
        if not terms['grace_years'].is_integer() or not terms['maturity_years'].is_integer():
            raise InputError("Grace and maturity must be whole years.")
    return {'delta_paths': normalized, 'terms': terms}


def zero_scenario(inspection):
    return {'delta_paths': {str(r): [0.0] * len(inspection['input_years']) for r in DELTA_ROWS}, 'terms': None}


def imported_scenario(inspection):
    values = inspection['customization']['delta_paths']
    return normalize_scenario({'delta_paths': values, 'terms': None}, inspection['input_years'])
