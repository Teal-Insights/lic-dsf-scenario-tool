"""Strict absolute comparison; spreadsheet errors are not numeric values."""
import math

ATOL = 1e-6
ERRORS = {"#NULL!", "#DIV/0!", "#VALUE!", "#REF!", "#NAME?", "#NUM!", "#N/A",
          "#GETTING_DATA", "#SPILL!", "#CALC!"}


def compare_one(expected, actual):
    def classify(value):
        if isinstance(value, str) and value.strip().upper() in ERRORS:
            return "error", value.strip().upper()
        if isinstance(value, bool):
            return "bool", value
        if isinstance(value, (int, float)):
            return "number", float(value)
        if value is None:
            return "empty", None
        return "text", str(value)
    left, x = classify(expected)
    right, y = classify(actual)
    if left != right:
        return False, f"type {left} vs {right}"
    if left == "number":
        return math.isfinite(x) and math.isfinite(y) and abs(x - y) <= ATOL, "absolute tolerance"
    return x == y, "error-class equality" if left == "error" else "exact equality"
