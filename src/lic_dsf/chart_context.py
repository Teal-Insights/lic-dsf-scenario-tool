"""Validation of deliberately shareable, source-bound chart context."""
from __future__ import annotations

import re
import unicodedata


LABEL_ERROR = (
    "Use a short chart label; fiscal years are allowed, but file paths, links "
    "and control characters are not."
)
RECORD_ERROR = "The chart context does not match a valid workbook and revision."
_FISCAL_YEAR = re.compile(
    r"(?<![\w/])(?:(?P<fy>FY) ?)?(?P<start>[0-9]{4}|[0-9]{2})/"
    r"(?P<end>[0-9]{4}|[0-9]{2})(?![\w/])", re.IGNORECASE
)
_LINK = re.compile(r"(?:https?|file|ftp|smb|mailto|javascript|data):|www\.", re.IGNORECASE)
_DRIVE = re.compile(r"(?<!\w)[A-Za-z]:")
_ARTIFACT = re.compile(r"\.(?:xlsx|xlsm|xls|csv|db|sqlite|sqlite3|json|pdf|png)\b", re.IGNORECASE)


def _mask_fiscal_year(match):
    start, end = match.group("start"), match.group("end")
    if len(start) == 2 and (not match.group("fy") or len(end) != 2):
        return match.group(0)
    expected = int(start) + 1
    if len(end) == 2:
        expected %= 100
    if int(end) != expected:
        return match.group(0)
    return "FISCAL_YEAR"


def normalize_context_label(value):
    """Return a canonical label, or None for an explicit blank/clear.

    Rejected content is never included in the error message. Fiscal-year slashes
    are the sole slash exception; labels are outward text, not paths or markup.
    """
    if value is None:
        return None
    if not isinstance(value, str) or any(not char.isprintable() for char in value):
        raise ValueError(LABEL_ERROR)
    label = unicodedata.normalize("NFC", value).strip()
    if not label:
        return None
    if len(label) > 80:
        raise ValueError("Use a chart label of at most 80 characters.")
    inspected = unicodedata.normalize("NFKC", label)
    if ("\\" in inspected or _LINK.search(inspected) or _DRIVE.search(inspected) or _ARTIFACT.search(inspected)
            or "/" in _FISCAL_YEAR.sub(_mask_fiscal_year, inspected)):
        raise ValueError(LABEL_ERROR)
    return label


def validate_chart_context(value, workbook_sha256):
    """Return only the three canonical fields, bound to the full source SHA."""
    if (not isinstance(workbook_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", workbook_sha256) is None
            or not isinstance(value, dict)
            or set(value) != {"workbook_sha256", "label", "revision"}
            or value["workbook_sha256"] != workbook_sha256
            or type(value["revision"]) is not int or value["revision"] < 0):
        raise ValueError(RECORD_ERROR)
    label = normalize_context_label(value["label"])
    if label != value["label"] or (value["revision"] == 0 and label is not None):
        raise ValueError(RECORD_ERROR)
    return {"workbook_sha256": workbook_sha256, "label": label, "revision": value["revision"]}
