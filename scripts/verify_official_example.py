"""Reproduce two official-example application regression cases.

This is not an independent Excel recalculation. Obtain the original illustrative
workbook separately, install this exact application, and run this script locally.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math


ATOL = 1e-6
OFFICIAL_SHA = "3a0a0b80c7cbc95ac953f25ecae0b437129d669ceb8aeefb54ab86dc8727ea86"
EXPECTED_FIELDS = {
    "contract_version", "workbook_sha256", "first_projection_year", "input_years",
    "scenario", "scenario_hash", "points", "thresholds", "evidence", "warnings",
}
RUN_FIELDS = {"engine_identity", "created_utc", "run_hash"}


def compare(expected, actual, path="result"):
    """Return checked leaf count or raise at the first structural/value mismatch."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or expected.keys() != actual.keys():
            raise ValueError(path + ": object fields differ")
        return sum(compare(expected[key], actual[key], path + "." + key)
                   for key in sorted(expected))
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(expected) != len(actual):
            raise ValueError(path + ": list length/type differs")
        return sum(compare(left, right, f"{path}[{index}]")
                   for index, (left, right) in enumerate(zip(expected, actual)))
    if isinstance(expected, bool) or isinstance(actual, bool):
        if type(expected) is not type(actual) or expected != actual:
            raise ValueError(path + ": boolean value/type differs")
    elif isinstance(expected, (int, float)):
        if (not isinstance(actual, (int, float)) or not math.isfinite(expected)
                or not math.isfinite(actual) or abs(expected - actual) > ATOL):
            raise ValueError(path + ": numerical value differs beyond fixed tolerance")
    elif type(expected) is not type(actual) or expected != actual:
        raise ValueError(path + ": value/type differs")
    return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--output", required=True, type=Path,
                        help="New local JSON receipt path; existing files are not overwritten.")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    fixture_path = root / "tests" / "fixtures" / "official-example-regression.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    if fixture.get("workbook_sha256") != OFFICIAL_SHA or fixture.get("atol") != ATOL:
        raise SystemExit("The regression reference is not the expected official-example contract.")
    if [case.get("case") for case in fixture.get("cases", [])] != ["control", "lower-growth"]:
        raise SystemExit("Both expected regression cases must be present.")
    if args.output.exists() or args.output.resolve() == args.workbook.resolve():
        raise SystemExit("Choose a new receipt path. Existing files are not overwritten.")
    before = hashlib.sha256(args.workbook.read_bytes()).hexdigest()
    if before != OFFICIAL_SHA:
        raise SystemExit("The workbook differs from the exact official illustrative download. No calculation was run.")
    from lic_dsf import calculate, engine_identity
    receipt = {"check": "official-example application regression",
               "fresh_excel_verification": "not performed",
               "workbook_sha256": before, "atol": ATOL,
               "fixture_sha256": hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
               "engine_identity": engine_identity(), "cases": []}
    for case in fixture["cases"]:
        expected = case["expected"]
        if set(expected) != EXPECTED_FIELDS:
            raise SystemExit("The regression reference is incomplete or has unexpected fields.")
        print("Calculating " + case["case"] + "...", flush=True)
        actual = calculate(args.workbook, expected["scenario"], expected_sha256=before)
        if set(actual) != EXPECTED_FIELDS | RUN_FIELDS:
            raise SystemExit("The calculated result contract changed; review is required.")
        count = compare(expected, {key: actual[key] for key in EXPECTED_FIELDS})
        receipt["cases"].append({"case": case["case"], "checked_leaves": count,
                                 "evidence": actual["evidence"], "passed": True})
        print(f"PASS {case['case']}: {count} checked values/fields", flush=True)
    if hashlib.sha256(args.workbook.read_bytes()).hexdigest() != before:
        raise SystemExit("Workbook changed during the check. No success receipt written.")
    receipt["passed"] = True
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print("PASS both application regression cases. Fresh Excel verification was not performed.")


if __name__ == "__main__":
    main()
