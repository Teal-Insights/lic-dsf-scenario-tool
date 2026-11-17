"""Read baked projection years and workbook year labels as one axis.

Generated formulas still iterate the template's year labels. Workbook inputs
are already labelled with the shifted years. While a calculation is active, a
lookup of the formula's current year adds or subtracts that one offset when
the caller and the series are on different labels. An issuance-year label
used as the time component is the template projection year for that vintage,
so it moves onto the series by the series offset. A time label that is the
neighbor of the formula's current year stays on the series. Other year
numbers stay as written. Offset 0 leaves every lookup unchanged. A series
whose years are not the baked labels or those labels plus the offset is left
unchanged, and the original lookup can still raise.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar

_DELTA = ContextVar('projection_year_delta', default=0)
_CALLER = ContextVar('projection_year_caller', default=None)
_YEAR = ContextVar('projection_year_key', default=None)
_ISSUANCE = ContextVar('projection_year_issuance', default=None)
_BAKED_BY_ID = {}
_BAKED_KEYS = None
_SNAPSHOT = None
_ISSUANCE_KEYS = None
_INSTALLED = False


def install():
    """Patch generated lookups once. Inactive until a calculation sets an offset."""
    global _INSTALLED
    if _INSTALLED:
        return
    from lic_dsf_2025_08_12 import internals, runtime
    from lic_dsf_2025_08_12.tensor import Tensor
    _ensure_baked_keys()
    Tensor.__getitem__ = _wrap_method(Tensor.__getitem__, _translate_item)
    Tensor.sel = _wrap_method(Tensor.sel, _translate_selection)
    runtime.CoordinateReader.__getitem__ = _wrap_method(
        runtime.CoordinateReader.__getitem__, _translate_reader
    )
    runtime.evaluate = _translate_evaluate(runtime.evaluate)
    internals.evaluate = runtime.evaluate
    _INSTALLED = True


def uniform_delta(series):
    """Return the constant year offset from the old-debt snapshot, or None."""
    from lic_dsf_2025_08_12.tensor import DomainError, Series
    if not isinstance(series, Series):
        return None
    try:
        keys = series.domain.axis('TIME_PERIOD').keys
    except DomainError:
        return None
    snapshot = _snapshot()
    if len(keys) != len(snapshot):
        return None
    if any(type(key) is not int or type(snap) is not int for key, snap in zip(keys, snapshot)):
        return None
    offsets = {key - snap for key, snap in zip(keys, snapshot)}
    if len(offsets) != 1:
        return None
    return offsets.pop()


@contextmanager
def shifted_projection(delta):
    """Activate one projection offset. Zero leaves lookups unchanged."""
    install()
    if not delta:
        yield
        return
    token = _DELTA.set(delta)
    try:
        yield
    finally:
        _DELTA.reset(token)


@contextmanager
def projection_years(model):
    """Activate translation for one workbook whose old-debt years share one offset."""
    delta = uniform_delta(getattr(model, 'input3_old_debt_service', None))
    with shifted_projection(delta or 0):
        yield


@contextmanager
def workbook_caller():
    """Mark chart-year reads as workbook labels for the duration of one selection."""
    delta = _DELTA.get()
    if not delta:
        yield
        return
    token = _CALLER.set(delta)
    try:
        yield
    finally:
        _CALLER.reset(token)


@contextmanager
def template_caller():
    """Mark reads as baked template labels for the duration of one formula."""
    delta = _DELTA.get()
    if not delta:
        yield
        return
    token = _CALLER.set(0)
    try:
        yield
    finally:
        _CALLER.reset(token)


def _wrap_method(original, wrapper):
    def patched(self, *args, **kwargs):
        return wrapper(original, self, *args, **kwargs)
    patched._projection_year_shift = True
    return patched


def _translate_item(original, self, key):
    if not _DELTA.get() or _CALLER.get() is None:
        return original(self, key)
    return original(self, _shifted_key(key, self, _series_id(self)))


def _translate_selection(original, self, **selectors):
    delta = _DELTA.get()
    caller = _CALLER.get()
    if not delta or caller is None or 'TIME_PERIOD' not in selectors:
        return original(self, **selectors)
    space = _space_of_domain(self.domain, _series_id(self))
    if space is None or space == caller or type(selectors['TIME_PERIOD']) is not int:
        return original(self, **selectors)
    selectors = dict(selectors)
    selectors['TIME_PERIOD'] = selectors['TIME_PERIOD'] + (space - caller)
    return original(self, **selectors)


def _translate_reader(original, self, key):
    delta = _DELTA.get()
    if not delta:
        return original(self, key)
    caller = _CALLER.get()
    space = _space_of_domain(self.domain, self._series_id)
    if caller is not None and space is not None and space != caller:
        key = _shifted_key(key, self, self._series_id, force=True)
    caller_token = _CALLER.set(_caller_space(self.domain, space))
    year_token = _YEAR.set(_coordinate_year(key, self.domain))
    issuance_token = _ISSUANCE.set(_axis_value(key, self.domain, 'ISSUANCE_YEAR'))
    try:
        return original(self, key)
    finally:
        _ISSUANCE.reset(issuance_token)
        _YEAR.reset(year_token)
        _CALLER.reset(caller_token)


def _translate_evaluate(original):
    def evaluate(formula, domain):
        delta = _DELTA.get()
        if not delta:
            return original(formula, domain)
        from lic_dsf_2025_08_12.excel import XlError
        space = _space_of_domain(domain)
        caller_space = _caller_space(domain, space)

        def generate():
            caller_token = _CALLER.set(caller_space)
            try:
                for coordinate in domain:
                    year_token = _YEAR.set(_coordinate_year(coordinate, domain))
                    issuance_token = _ISSUANCE.set(_axis_value(coordinate, domain, 'ISSUANCE_YEAR'))
                    try:
                        try:
                            yield coordinate, formula(*coordinate)
                        except XlError as error:
                            yield coordinate, error.code
                    finally:
                        _ISSUANCE.reset(issuance_token)
                        _YEAR.reset(year_token)
            finally:
                _CALLER.reset(caller_token)

        return generate()
    evaluate._projection_year_shift = True
    return evaluate


def _shifted_key(key, values, series_id, force=False):
    caller = _CALLER.get()
    space = _space_of_domain(values.domain, series_id)
    if caller is None or space is None:
        return key
    coordinate = key if isinstance(key, tuple) else (key,)
    index = _year_index(values.domain)
    if index is None or index >= len(coordinate) or type(coordinate[index]) is not int:
        return key
    year = coordinate[index]
    if space != caller and _follows_caller(year, force):
        return _replace_year(key, coordinate, index, year + (space - caller))
    vintage = _vintage_time(year, coordinate, values.domain, space)
    if vintage is None:
        return key
    return _replace_year(key, coordinate, index, vintage)


def _follows_caller(year, force):
    """Shift the formula year, a direct read, or a reader coordinate."""
    if force:
        return True
    current = _YEAR.get()
    if current is None:
        return _ISSUANCE.get() is None
    return year == current


def _vintage_time(year, coordinate, domain, space):
    """Map a template issuance label onto this series, or return None."""
    if type(year) is not int or year not in _issuance_keys():
        return None
    local = _axis_value(coordinate, domain, 'ISSUANCE_YEAR')
    single_time = _year_index(domain) == 0 and len(getattr(domain, 'axes', ())) == 1
    if local != year and not (local is None and single_time and _ISSUANCE.get() == year):
        return None
    if _adjacent_year(year, domain):
        return None
    return year + space


def _adjacent_year(year, domain):
    current = _YEAR.get()
    keys = _domain_time_keys(domain)
    if type(current) is not int or not keys or year not in keys or current not in keys:
        return False
    return abs(keys.index(year) - keys.index(current)) == 1


def _replace_year(key, coordinate, index, year):
    updated = list(coordinate)
    updated[index] = year
    shifted = tuple(updated)
    return shifted if isinstance(key, tuple) else shifted[0]


def _caller_space(domain, space):
    if space is not None:
        return space
    if _has_axis(domain, 'ISSUANCE_YEAR'):
        return 0
    return None


def _has_axis(domain, name):
    return any(getattr(axis, 'name', None) == name for axis in getattr(domain, 'axes', ()))


def _axis_value(key, domain, name):
    coordinate = key if isinstance(key, tuple) else (key,)
    for index, axis in enumerate(getattr(domain, 'axes', ())):
        if getattr(axis, 'name', None) == name and index < len(coordinate):
            return coordinate[index]
    return None


def _issuance_keys():
    global _ISSUANCE_KEYS
    if _ISSUANCE_KEYS is None:
        from lic_dsf_2025_08_12 import data
        _ISSUANCE_KEYS = frozenset(data.ISSUANCE_YEAR_AXIS.keys)
    return _ISSUANCE_KEYS


def _coordinate_year(key, domain):
    coordinate = key if isinstance(key, tuple) else (key,)
    index = _year_index(domain)
    if index is None or index >= len(coordinate) or type(coordinate[index]) is not int:
        return None
    return coordinate[index]


def _series_id(series):
    schema = getattr(series, 'schema', None)
    return getattr(schema, 'series_id', None)


def _space_of_domain(domain, series_id=None):
    keys = _domain_time_keys(domain)
    delta = _DELTA.get()
    if keys is None or not delta:
        return None
    baked = _baked_keys(series_id) if series_id else None
    if baked is not None:
        if keys == baked:
            return 0
        if _shifted(keys, baked, delta):
            return delta
        return None
    _ensure_baked_keys()
    template = keys in _BAKED_KEYS
    workbook = _shifted_into_baked(keys, delta)
    if template and workbook:
        return None
    if template:
        return 0
    if workbook:
        return delta
    return None


def _shifted(keys, baked, delta):
    return (
        len(keys) == len(baked)
        and all(type(key) is int and type(snap) is int and key - snap == delta for key, snap in zip(keys, baked))
    )


def _shifted_into_baked(keys, delta):
    if any(type(key) is not int for key in keys):
        return False
    return tuple(key - delta for key in keys) in _BAKED_KEYS


def _domain_time_keys(domain):
    from lic_dsf_2025_08_12.tensor import AxisTemplate
    axes = getattr(domain, 'axes', None)
    if not axes:
        return None
    for axis in axes:
        if getattr(axis, 'name', None) != 'TIME_PERIOD':
            continue
        if isinstance(axis, AxisTemplate):
            return tuple(axis.snapshot)
        keys = getattr(axis, 'keys', None)
        if keys is None:
            return None
        return tuple(keys)
    return None


def _baked_keys(series_id):
    if series_id in _BAKED_BY_ID:
        return _BAKED_BY_ID[series_id]
    from lic_dsf_2025_08_12 import data
    spec = getattr(data, series_id.upper(), None) if series_id else None
    keys = _time_keys(spec) if spec is not None else None
    _BAKED_BY_ID[series_id] = keys
    return keys


def _time_keys(spec):
    from lic_dsf_2025_08_12.tensor import Domain, DomainTemplate
    domain = spec if isinstance(spec, (Domain, DomainTemplate)) else None
    if domain is None:
        required = getattr(spec, 'required', None)
        if isinstance(required, (Domain, DomainTemplate)):
            domain = required
        else:
            schema = getattr(spec, 'schema', None)
            domain = getattr(schema, 'domain', None)
    return _domain_time_keys(domain)


def _ensure_baked_keys():
    global _BAKED_KEYS
    if _BAKED_KEYS is not None:
        return
    from lic_dsf_2025_08_12 import data
    found = set()
    for name in dir(data):
        if not name.isupper():
            continue
        keys = _time_keys(getattr(data, name))
        if keys is not None:
            found.add(keys)
            _BAKED_BY_ID.setdefault(name.lower(), keys)
    _BAKED_KEYS = found


def _year_index(domain):
    for index, axis in enumerate(getattr(domain, 'axes', ())):
        if getattr(axis, 'name', None) == 'TIME_PERIOD':
            return index
    return None


def _snapshot():
    global _SNAPSHOT
    if _SNAPSHOT is None:
        keys = _baked_keys('input3_old_debt_service')
        if keys is None:
            raise RuntimeError('old debt service year snapshot is missing')
        _SNAPSHOT = keys
    return _SNAPSHOT
