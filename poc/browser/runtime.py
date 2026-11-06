"""Browser-side calculation helpers.

The workbook bytes stay in this page's memory. Nothing here opens a network
connection or writes the analyst's file.
"""
from __future__ import annotations

import json
from importlib.metadata import distribution
from pathlib import Path

LIBRARY_COMMIT = "e0f5a8c2359e6931bb43adfdcb16a754232b2ffd"
LIBRARY_URL = "https://github.com/Teal-Insights/lic-dsf-2025-08-12"


def ensure_provenance():
    """Record the pinned library commit for a wheel that was not a VCS install."""
    dist = distribution("lic-dsf-2025-08-12")
    target = Path(str(dist.locate_file("direct_url.json")))
    if target.is_file():
        recorded = json.loads(target.read_text(encoding="utf-8"))
        commit = (recorded.get("vcs_info") or {}).get("commit_id")
        if commit != LIBRARY_COMMIT:
            raise RuntimeError("engine_source_revision_unverified")
        return
    target.write_text(json.dumps({
        "url": LIBRARY_URL,
        "vcs_info": {
            "commit_id": LIBRARY_COMMIT,
            "requested_revision": LIBRARY_COMMIT,
            "vcs": "git",
        },
    }, sort_keys=True), encoding="utf-8")


def prepare():
    ensure_provenance()
    import lic_dsf
    from lic_dsf_2025_08_12 import Model
    return {
        "app": lic_dsf.__file__,
        "model": Model.__module__,
    }


def inspect_upload(path):
    from lic_dsf.illustrative import builtin_investment_cases
    from lic_dsf.scenarios import zero_scenario
    from lic_dsf.workbooks import inspect_workbook

    info = inspect_workbook(path)
    status = info["compatibility"]["status"]
    cases = []
    if status == "supported":
        cases.append({
            "id": "zero",
            "title": "Zero adjustment",
            "definition": zero_scenario(info),
        })
        for case in builtin_investment_cases(info["workbook_sha256"], info["input_years"]):
            cases.append({
                "id": case["id"],
                "title": case["title"],
                "definition": case["scenario_file"]["definition"],
            })
    return json.dumps({
        "sha": info["workbook_sha256"],
        "status": status,
        "errors": list(info["compatibility"]["errors"]),
        "warnings": list(info["warnings"]),
        "first_year": info["first_projection_year"],
        "years": list(info["input_years"]),
        "cases": cases,
    })


def calculate_upload(path, scenario_json):
    from lic_dsf import calculate
    from lic_dsf.workbooks import file_hash

    scenario = json.loads(scenario_json)
    sha = file_hash(path)
    return json.dumps(calculate(path, scenario, expected_sha256=sha))
