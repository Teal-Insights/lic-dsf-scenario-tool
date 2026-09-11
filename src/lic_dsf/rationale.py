"""Deliberately shared explanations, separate from private journals and inputs."""
import unicodedata

DRIVERS = {
    '11': 'Revenue and grants', '13': 'Primary expenditure', '15': 'Grants',
    '17': 'Public sector assets', '20': 'Real GDP growth', '22': 'GDP deflator inflation',
    '24': 'Nominal depreciation', '28': 'Exports', '30': 'Imports',
    '32': 'Official current transfers', '34': 'Private current transfers',
    '36': 'Net foreign direct investment', '38': 'GDP deflator in US dollars',
    'financing': 'External financing terms',
}


def normalize_rationale(value):
    if not isinstance(value, dict) or any(key not in DRIVERS for key in value):
        raise ValueError('Shared explanations must use the supported input names.')
    result = {}
    for key, text in value.items():
        if (not isinstance(text, str) or len(text) > 1500
                or any(not c.isprintable() and c != '\n' for c in text)):
            raise ValueError('Use plain text of at most 1,500 characters per shared explanation.')
        text = unicodedata.normalize('NFC', text).strip()
        if text:
            result[key] = text
    return result


def rationale_entries(definition, value):
    """Include every changed driver and every deliberately provided explanation."""
    notes = normalize_rationale(value)
    changed = {str(key) for key, values in definition.get('delta_paths', {}).items()
               if any(v != 0 for v in values)}
    if definition.get('terms') is not None:
        changed.add('financing')
    return [{'driver': key, 'label': label, 'changed': key in changed,
             'text': notes.get(key, 'No explanation provided.')}
            for key, label in DRIVERS.items() if key in changed or key in notes]
