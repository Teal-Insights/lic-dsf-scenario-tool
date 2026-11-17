"""Calculate a workbook whose projection years are a constant shift from 2024.

The pinned generated library bakes the template calendar into year literals
and into the domains it walks. A supported workbook whose cached year headers
all move by the same amount is calculated on those workbook years. Loading a
workbook stays on the library's own reader. The shift applies only while a
result is sampled, and a 2024 workbook is unchanged.
"""
from __future__ import annotations

import contextvars
from contextlib import contextmanager
import inspect
import io
import tokenize

from .workbooks import IntakeError

TEMPLATE_FIRST_YEAR = 2024
_YEAR_MIN = 1900
_YEAR_MAX = 2200
_SHIFT = contextvars.ContextVar("lic_dsf_projection_shift", default=0)

_installed = False
_template_ids = {}
_shifted_domains = {}
_compiled = {}
_originals = None
_depth = 0
_active_shift = None


def _year_indexes(domain):
    indexes = []
    for index, axis in enumerate(domain.axes):
        keys = axis.keys
        if (
            axis.key_type is int
            and keys
            and all(isinstance(key, int) and _YEAR_MIN <= key <= _YEAR_MAX for key in keys)
        ):
            indexes.append(index)
    return indexes


def _is_year_axis(axis):
    keys = getattr(axis, "keys", ())
    return (
        getattr(axis, "key_type", None) is int
        and bool(keys)
        and all(isinstance(key, int) and _YEAR_MIN <= key <= _YEAR_MAX for key in keys)
    )


def _both_ways(expected, actual):
    exp = set(expected)
    act = set(actual)
    return any(key not in exp for key in act) and any(key not in act for key in exp)


def _shift_domain(domain):
    from lic_dsf_2025_08_12.tensor import Axis, Domain

    shift = _SHIFT.get()
    indexes = _template_ids.get(id(domain))
    if shift == 0 or indexes is None:
        return domain
    key = (id(domain), shift)
    cached = _shifted_domains.get(key)
    if cached is not None:
        return cached
    index_set = set(indexes)
    new_axes = tuple(
        Axis(axis.name, tuple(year + shift for year in axis.keys), int) if i in index_set else axis
        for i, axis in enumerate(domain.axes)
    )
    if domain.coordinates is None:
        shifted = Domain.product(*new_axes)
    else:
        coords = []
        for coord in domain.coordinates:
            updated = list(coord)
            for index in indexes:
                updated[index] = updated[index] + shift
            coords.append(tuple(updated))
        shifted = Domain.explicit(axes=new_axes, coordinates=coords)
    _shifted_domains[key] = shifted
    return shifted


def _shift_key(key, shift):
    if isinstance(key, tuple):
        return tuple(
            part + shift if isinstance(part, int) and _YEAR_MIN <= part <= _YEAR_MAX else part
            for part in key
        )
    if isinstance(key, int) and _YEAR_MIN <= key <= _YEAR_MAX:
        return key + shift
    return key


def _retarget_keys(values, axis_name, keys):
    from lic_dsf_2025_08_12.tensor import DomainError

    shift = _SHIFT.get()
    if not shift:
        return keys
    domain = getattr(values, "domain", None)
    if domain is None:
        return keys
    try:
        axis = domain.axis(axis_name)
    except DomainError:
        return keys
    if axis.key_type is not int:
        return keys
    present = set(axis.keys)
    if all(not isinstance(key, int) or key in present for key in keys):
        return keys
    shifted = tuple(
        key + shift if isinstance(key, int) and _YEAR_MIN <= key <= _YEAR_MAX else key for key in keys
    )
    if all(not isinstance(key, int) or key in present for key in shifted):
        return shifted
    return keys


def _align_kwargs(kwargs):
    import lic_dsf_2025_08_12.tensor as tensor
    from lic_dsf_2025_08_12.tensor import Axis, AxisTemplate, SchemaTemplate

    out = dict(kwargs)
    shift = _SHIFT.get()
    for key, value in kwargs.items():
        schema = getattr(value, "schema", None)
        if isinstance(schema, SchemaTemplate):
            labellers = {}
            for axis in schema.domain.axes:
                if (
                    isinstance(axis, AxisTemplate)
                    and axis.labeller in kwargs
                    and isinstance(kwargs[axis.labeller], tensor.Tensor)
                ):
                    labellers[axis.name] = kwargs[axis.labeller]
            current = tensor.align_runtime_keys(value, **labellers) if labellers else value
            if shift and isinstance(current, tensor.Series):
                replacements = {}
                for axis in schema.domain.axes:
                    if isinstance(axis, Axis) and _is_year_axis(axis):
                        actual = current.domain.axis(axis.name)
                        if actual.keys == axis.keys:
                            replacements[axis.name] = Axis(
                                axis.name, tuple(year + shift for year in axis.keys), int
                            )
                if replacements:
                    current = tensor.relabel_series(current, **replacements)
            out[key] = current
            continue
        if shift and isinstance(value, tensor.Series) and id(value.domain) in _template_ids:
            replacements = {}
            for index in _template_ids[id(value.domain)]:
                axis = value.domain.axes[index]
                replacements[axis.name] = Axis(
                    axis.name, tuple(year + shift for year in axis.keys), int
                )
            out[key] = tensor.relabel_series(value, **replacements)
    return out


def _rewrite(source, shift):
    tokens = []
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type == tokenize.NUMBER and tok.string.isdigit():
            year = int(tok.string)
            if 1990 <= year <= _YEAR_MAX:
                moved = year + shift
                if not _YEAR_MIN <= moved <= _YEAR_MAX:
                    raise IntakeError("projection_year_shift_out_of_range")
                tok = tok._replace(string=str(moved))
        tokens.append(tok)
    return tokenize.untokenize(tokens)


def _compiled_functions(shift):
    import lic_dsf_2025_08_12.internals as internals

    cached = _compiled.get(shift)
    if cached is not None:
        return cached
    namespace = dict(internals.__dict__)
    source = _rewrite(inspect.getsource(internals), shift)
    exec(compile(source, internals.__file__, "exec"), namespace)
    wrapped = {}
    for name, fn in namespace.items():
        if not inspect.isfunction(fn) or fn.__module__ != internals.__name__:
            continue

        def wrap(fn=fn):
            def wrapped(*args, **kwargs):
                if kwargs:
                    kwargs = _align_kwargs(kwargs)
                return fn(*args, **kwargs)

            return wrapped

        wrapped[name] = wrap()
    _compiled[shift] = wrapped
    return wrapped


def _install():
    global _installed
    if _installed:
        return
    import lic_dsf_2025_08_12.data as data
    import lic_dsf_2025_08_12.runtime as runtime
    import lic_dsf_2025_08_12.tensor as tensor
    from lic_dsf_2025_08_12.excel import XlError
    from lic_dsf_2025_08_12.tensor import (
        Axis,
        CoordinateError,
        Domain,
        DomainError,
        SchemaTemplate,
        TensorSchema,
    )

    for value in vars(data).values():
        domains = [value] if isinstance(value, Domain) else []
        schema = getattr(value, "schema", None)
        for attr in ("domain", "required"):
            item = getattr(value, attr, None)
            if isinstance(item, Domain):
                domains.append(item)
        item = getattr(schema, "domain", None)
        if isinstance(item, Domain):
            domains.append(item)
        for domain in domains:
            indexes = _year_indexes(domain)
            if indexes:
                _template_ids[id(domain)] = tuple(indexes)

    original_bound = tensor._bound_axis

    def bound_axis(axis, labellers):
        bound = original_bound(axis, labellers)
        shift = _SHIFT.get()
        if shift and isinstance(axis, Axis) and _is_year_axis(bound):
            return Axis(bound.name, tuple(year + shift for year in bound.keys), int)
        return bound

    tensor._bound_axis = bound_axis

    original_schema_validate = SchemaTemplate.validate

    def schema_validate(self, tensor_value, *, exact=False):
        shift = _SHIFT.get()
        if shift == 0 or not isinstance(tensor_value, tensor.Tensor):
            return original_schema_validate(self, tensor_value, exact=exact)
        new_axes = []
        changed = False
        for axis in self.domain.axes:
            if isinstance(axis, Axis) and _is_year_axis(axis):
                try:
                    actual = tensor_value.domain.axis(axis.name)
                except DomainError:
                    actual = None
                shifted_keys = tuple(year + shift for year in axis.keys)
                if (
                    actual is not None
                    and _both_ways(axis.keys, actual.keys)
                    and not _both_ways(shifted_keys, actual.keys)
                ):
                    new_axes.append(Axis(axis.name, shifted_keys, int))
                    changed = True
                    continue
            new_axes.append(axis)
        if not changed:
            return original_schema_validate(self, tensor_value, exact=exact)
        shifted_schema = SchemaTemplate(
            self.series_id,
            tensor.DomainTemplate(tuple(new_axes), self.domain.coordinates),
            self.value_types,
        )
        return original_schema_validate(shifted_schema, tensor_value, exact=exact)

    SchemaTemplate.validate = schema_validate

    original_tensor_validate = TensorSchema.validate

    def tensor_validate(self, tensor_value, *, exact=False):
        shift = _SHIFT.get()
        indexes = _template_ids.get(id(self.domain)) if shift else None
        schema = self
        if indexes and isinstance(tensor_value, tensor.Tensor):
            template_keys = self.domain.axes[indexes[0]].keys
            actual_keys = tensor_value.domain.axes[indexes[0]].keys
            shifted_keys = tuple(year + shift for year in template_keys)
            if _both_ways(template_keys, actual_keys) and not _both_ways(shifted_keys, actual_keys):
                schema = TensorSchema(self.series_id, _shift_domain(self.domain), self.value_types)
        token = _SHIFT.set(0)
        try:
            return original_tensor_validate(schema, tensor_value, exact=exact)
        finally:
            _SHIFT.reset(token)

    TensorSchema.validate = tensor_validate

    original_init = runtime.CoordinateReader.__init__

    def init(self, series_id, domain, compute):
        original_init(self, series_id, _shift_domain(domain), compute)

    runtime.CoordinateReader.__init__ = init

    original_iter = tensor.Domain.__iter__

    def iterate(self):
        shifted = _shift_domain(self)
        if shifted is not self:
            return original_iter(shifted)
        return original_iter(self)

    tensor.Domain.__iter__ = iterate

    def items(self):
        return zip(original_iter(self.domain), self._values, strict=True)

    tensor.Tensor.items = items

    original_get = tensor.Tensor.__getitem__

    def getitem(self, key):
        try:
            return original_get(self, key)
        except CoordinateError:
            shift = _SHIFT.get()
            if not shift:
                raise
            shifted = _shift_key(key, shift)
            if shifted == key:
                raise
            return original_get(self, shifted)

    tensor.Tensor.__getitem__ = getitem

    original_reader_get = runtime.CoordinateReader.__getitem__

    def reader_get(self, key):
        try:
            return original_reader_get(self, key)
        except CoordinateError:
            shift = _SHIFT.get()
            if not shift:
                raise
            shifted = _shift_key(key, shift)
            if shifted == key:
                raise
            return original_reader_get(self, shifted)

    runtime.CoordinateReader.__getitem__ = reader_get

    original_view = runtime.view

    def view(values, rows=None, cols=None, *, cols_first=False):
        if isinstance(rows, dict) or isinstance(cols, dict):
            if isinstance(rows, dict):
                rows = {
                    name: _retarget_keys(values, name, tuple(keys)) for name, keys in rows.items()
                }
            if isinstance(cols, dict):
                cols = {
                    name: _retarget_keys(values, name, tuple(keys)) for name, keys in cols.items()
                }
            return original_view(values, rows, cols, cols_first=cols_first)
        axes = getattr(getattr(values, "domain", None), "axes", ())
        if rows is not None and cols is not None and len(axes) >= 2:
            row_axis, col_axis = (axes[1], axes[0]) if cols_first else (axes[0], axes[1])
            rows = _retarget_keys(values, row_axis.name, tuple(rows))
            cols = _retarget_keys(values, col_axis.name, tuple(cols))
        elif cols is not None and rows is None and axes:
            cols = _retarget_keys(values, axes[0].name, tuple(cols))
        elif rows is not None and cols is None and axes:
            rows = _retarget_keys(values, axes[0].name, tuple(rows))
        return original_view(values, rows, cols, cols_first=cols_first)

    runtime.view = view

    original_span = runtime.span

    def span(axis, first, last):
        try:
            return original_span(axis, first, last)
        except XlError:
            shift = _SHIFT.get()
            if not shift or not isinstance(first, int) or not isinstance(last, int):
                raise
            return original_span(axis, first - shift, last - shift)

    runtime.span = span

    original_collect = tensor._collect_series

    def collect(series_type, schema, cells, records, domain):
        if isinstance(domain, Domain):
            shifted = _shift_domain(domain)
            if shifted is not domain and isinstance(schema, TensorSchema):
                schema = TensorSchema(schema.series_id, shifted, schema.value_types)
            domain = shifted
        elif domain is None and isinstance(getattr(schema, "domain", None), Domain):
            shifted = _shift_domain(schema.domain)
            if shifted is not schema.domain and isinstance(schema, TensorSchema):
                schema = TensorSchema(schema.series_id, shifted, schema.value_types)
                domain = shifted
        return original_collect(series_type, schema, cells, records, domain)

    tensor._collect_series = collect
    _installed = True


def _activate(shift):
    global _originals
    import lic_dsf_2025_08_12.internals as internals

    functions = _compiled_functions(shift)
    if _originals is None:
        _originals = {name: getattr(internals, name) for name in functions}
    for name, fn in functions.items():
        setattr(internals, name, fn)


def _restore():
    import lic_dsf_2025_08_12.internals as internals

    for name, fn in _originals.items():
        setattr(internals, name, fn)


@contextmanager
def projection_axis(first_year):
    """Sample library results on `first_year` instead of the template's 2024."""
    global _depth, _active_shift
    if isinstance(first_year, bool) or not isinstance(first_year, int):
        raise IntakeError("projection_year_out_of_range")
    if not _YEAR_MIN <= first_year <= 2100:
        raise IntakeError("projection_year_out_of_range")
    shift = first_year - TEMPLATE_FIRST_YEAR
    if shift == 0:
        yield
        return
    _install()
    if _depth and _active_shift != shift:
        raise IntakeError("projection_year_shift_conflict")
    token = _SHIFT.set(shift)
    entered = _depth == 0
    try:
        if entered:
            _activate(shift)
            _active_shift = shift
        _depth += 1
        yield
    finally:
        if _depth:
            _depth -= 1
        _SHIFT.reset(token)
        if entered and _originals is not None:
            _restore()
            _active_shift = None
