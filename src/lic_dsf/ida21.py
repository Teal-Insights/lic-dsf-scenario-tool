"""Narrow IDA21 input and sampled-output geometry, checked at intake."""
PUBLIC = "Customized Scenario - public"
EXTERNAL = "Customized Scenario-External"
EXT_OUTPUT = "Output 3-1 Stress-external"
PUB_OUTPUT = "Output 3-2 Stress-public"
EXTRA_SHEETS = ("BLEND floating calculations WB", "Dom_Debt_Data", "Dom_Debt_Indicators")
# (delta row, level row, label fragment, neutral display name, units)
INPUTS = (
    (11, 10, "revenue and grants", "Revenue and grants", "percentage points of GDP"),
    (13, 12, "primary", "Primary expenditure", "percentage points of GDP"),
    (15, 14, "grants", "Grants", "percentage points of GDP"),
    (17, 16, "public sector assets", "Public sector assets", "local currency (workbook scale)"),
    (20, 19, "real gdp growth", "Real GDP growth", "percentage points"),
    (22, 21, "inflation rate", "GDP deflator inflation", "percentage points"),
    (24, 23, "nominal depreciation", "Nominal depreciation", "percentage points"),
    (28, 27, "exports", "Exports", "percentage points of GDP"),
    (30, 29, "imports", "Imports", "percentage points of GDP"),
    (32, 31, "net current transfers, official", "Official current transfers", "percentage points of GDP"),
    (34, 33, "net current transfers, private", "Private current transfers", "percentage points of GDP"),
    (36, 35, "net fdi", "Net foreign direct investment", "percentage points of GDP"),
    (38, 37, "gdp deflator in us dollar", "GDP deflator in US dollars", "percentage points"),
)
DELTA_ROWS = tuple(item[0] for item in INPUTS)
TERMS = {"rate": "C21", "grace_years": "C23", "maturity_years": "C24"}
# Values are sampled directly from the same template tables, not interpolated.
OFFSETS = (0, 2, 5, 10, 15, 20)
# metric, title, denominator, sheet, baseline row, custom row, first column, header row
METRICS = (
    ("ext_pv_gdp", "PV of PPG external debt-to-GDP ratio", "percent of GDP", EXT_OUTPUT, 11, 15, 3, 6),
    ("ext_pv_exports", "PV of PPG external debt-to-exports ratio", "percent of exports", EXT_OUTPUT, 35, 39, 3, 6),
    ("ext_ds_exports", "PPG external debt service-to-exports ratio", "percent of exports", EXT_OUTPUT, 59, 63, 3, 6),
    ("ext_ds_revenue", "PPG external debt service-to-revenue ratio", "percent of revenue", EXT_OUTPUT, 83, 87, 3, 6),
    ("public_pv_gdp", "PV of total public debt-to-GDP ratio", "percent of GDP", PUB_OUTPUT, 12, 16, 4, 8),
    ("public_pv_revenue", "PV of total public debt-to-revenue ratio", "percent of revenue", PUB_OUTPUT, 36, 40, 4, 8),
)
THRESHOLDS = (
    ("ext_pv_gdp", "I11", "H11", "gdp"),
    ("ext_pv_exports", "I10", "H10", "exports"),
    ("ext_ds_exports", "I13", "H13", "exports"),
    ("ext_ds_revenue", "I14", "H14", "revenue"),
    ("public_pv_gdp", "L9", "K9", "pv of total public debt"),
)
SENTINELS = (("external_rating", "Output 7 - Risk rating summary", "E48"),
             ("overall_rating", "Output 7 - Risk rating summary", "E54"),
             ("external_signal", "Chart Data", "D10"),
             ("selected_shock", "Chart Data", "D14"))


def cell(column: int, row: int) -> str:
    letters = ""
    while column:
        column, rem = divmod(column - 1, 26)
        letters = chr(65 + rem) + letters
    return letters + str(row)


def probes() -> list[dict]:
    result = []
    for metric, title, units, sheet, base, custom, col, header in METRICS:
        for offset in OFFSETS:
            for role, row in (("reference_baseline", base), ("customized", custom)):
                result.append({"id": f"{metric}:{offset}:{role}", "metric": metric,
                               "offset": offset, "role": role, "units": units,
                               "sheet": sheet, "cell": cell(col + offset, row)})
    result += [{"id": f"sentinel:{name}", "role": "sentinel", "sheet": sheet, "cell": address}
               for name, sheet, address in SENTINELS]
    return result
