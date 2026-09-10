"""JSON contracts for a local, workbook-specific calculation."""
from __future__ import annotations

from typing import TypedDict

CONTRACT_VERSION = "ida21-local-v1"


class Scenario(TypedDict):
    delta_paths: dict[str, list[float]]
    terms: dict[str, float] | None


class Point(TypedDict):
    metric: str
    year: int
    units: str
    reference_baseline: float | str | None
    as_supplied_customized: float | str | None
    scenario: float | str | None
    source_cells: dict[str, str]


class Calculation(TypedDict):
    contract_version: str
    workbook_sha256: str
    first_projection_year: int
    input_years: list[int]
    engine_identity: dict
    scenario: Scenario | None
    scenario_hash: str
    points: list[Point]
    thresholds: dict
    evidence: dict
    warnings: list[str]
    run_hash: str
