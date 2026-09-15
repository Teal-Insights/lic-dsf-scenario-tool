"""Complete teaching assumptions for the byte-identical official worked example.

These are application-authored illustrations, not the World Bank workbook itself.
No results or evidence are supplied: each chosen case becomes an editable draft.
"""
import hashlib
import json
from importlib.resources import files

from .rationale import normalize_rationale
from .scenarios import normalize_scenario

OFFICIAL_SHA256 = '3a0a0b80c7cbc95ac953f25ecae0b437129d669ceb8aeefb54ab86dc8727ea86'
OFFICIAL_YEARS = tuple(range(2024, 2045))
_CASES = (
    ('no-investment', '1. No investment · comparison case',
     'Start here. All macro adjustments are zero. New external financing is set '
     'to 8% interest, 4 years of grace and 9 years to maturity. Save and calculate '
     'this case first; measure the two investment cases against it.',
     '3aa0ad09774bf35eb9e14255d61f11fa041ee60c62c76e1bb7d0388bb343046f'),
    ('earlier-benefit', '2. Investment · larger assumed benefit',
     'Upfront spending of 0.5% of baseline GDP in 2027–2029, followed by '
     'maintenance of 0.05% in 2030–2044. Assume growth is 0.2 percentage points '
     'higher in 2030–2034. Fiscal and import paths are supplied together; '
     'review their shared explanations. Financing matches No investment.',
     '85cff5289a25caa2da2f7a638df739ce458c47ac9f7088ab04515e5d2e0ecb02'),
    ('smaller-benefit', '3. Investment · smaller assumed benefit',
     'The same upfront investment and maintenance, with a smaller assumed '
     'growth benefit of 0.1 percentage points in 2030–2034. The complete linked '
     'fiscal and import paths are supplied together. Financing matches No investment. Compare with '
     'No investment and Larger assumed benefit.',
     '873ac66e41fbcdb2ffec6509b3d367270196e91deb0ff285bc9b894c80b8f9d0'),
)


def builtin_investment_cases(workbook_sha256, input_years):
    """Return fresh input-only packages for the exact example, or no choices.

    Fingerprints bind every input and explanation to the reviewed teaching
    package. Never remap these baseline-dependent paths to another workbook.
    """
    if (workbook_sha256 != OFFICIAL_SHA256
            or not isinstance(input_years, (list, tuple))
            or any(type(year) is not int for year in input_years)
            or tuple(input_years) != OFFICIAL_YEARS):
        return []
    result = []
    for key, title, description, expected_hash in _CASES:
        raw = files('lic_dsf').joinpath('illustrative_cases', key + '.json').read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected_hash:
            raise ValueError('The built-in illustrative assumptions failed their integrity check.')
        pack = json.loads(raw)
        if (pack['workbook_sha256'] != workbook_sha256
                or pack['input_years'] != list(OFFICIAL_YEARS)
                or set(pack) != {'format', 'workbook_sha256', 'input_years',
                                 'definition', 'share_label', 'shared_rationale'}
                or pack['format'] != 'lic-dsf-scenario-v1'):
            raise ValueError('The built-in illustrative assumptions do not match this workbook.')
        normalize_scenario(pack['definition'], input_years)
        normalize_rationale(pack['shared_rationale'])
        result.append({'id': key, 'title': title, 'description': description,
                       'scenario_file': pack})
    return result
