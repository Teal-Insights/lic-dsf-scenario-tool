# Check a workbook, input or output

This version recognizes the English World Bank LIC-DSF IDA21 layout, file version `08-12-2025`. Use a completed copy with the required formulas and saved values intact. A matching filename alone does not establish support.

[Documentation index](README.md) · [Worked tutorial](tutorial.md) · [Methods and evidence](methodology.md) · [JSON contracts](data-contract.md)

## What intake accepts

The browser accepts `.xlsm` or `.xlsx` workbook packages up to 25 MiB (26,214,400 bytes). The app inspects the contents. An `.xlsx` extension does not make a converted or unrelated workbook compatible, and older LIC-DSF layouts are outside this release's support.

The checks require the expected sheet names, input labels, additive input formulas, financing anchors, projection-year geometry, output formula locations and saved values. Formula-valued delta cells are refused for review; their cached values are not silently substituted as new assumptions. Recognized literal empty delta cells can be treated as zero only when the corresponding level formula directly adds that cell.

The first projection year comes from `Input 1 - Basics!C18`. The 21 input years must match row 7, columns E:Y, in `Customized Scenario - public`. The tool also checks the supporting debt-data sheets and output/sentinel sheets named in [the version-specific geometry](../src/lic_dsf/ida21.py). Public-sector assets require the recognized national-currency scale of millions or billions.

A structurally supported upload can calculate with pending exact-Excel evidence. This does not certify arbitrary formula edits. An unsupported upload should retain its original contents while a maintainer investigates the reported finding. Do not rename sheets or erase formulas to bypass intake.

## Enter annual adjustments

Each row below contains 21 explicit entries in columns E:Y of `Customized Scenario - public`. Row identifiers are also the string keys in exported `delta_paths`. All entries must be finite numbers. Use **0** for no additional adjustment and complete every blank before saving.

| Row / JSON key | Input | Entry units |
| --- | --- | --- |
| 11 | Revenue and grants | Percentage points of GDP |
| 13 | Primary expenditure | Percentage points of GDP |
| 15 | Grants | Percentage points of GDP |
| 17 | Public sector assets | Local currency, at the displayed workbook scale |
| 20 | Real GDP growth | Percentage points |
| 22 | GDP deflator inflation | Percentage points |
| 24 | Nominal depreciation | Percentage points |
| 28 | Exports | Percentage points of GDP |
| 30 | Imports | Percentage points of GDP |
| 32 | Official current transfers | Percentage points of GDP |
| 34 | Private current transfers | Percentage points of GDP |
| 36 | Net foreign direct investment | Percentage points of GDP |
| 38 | GDP deflator in US dollars | Percentage points |

An adjustment is added through the template's customized-scenario formula. It is not the resulting level. A growth adjustment of −0.5 percentage points changes an illustrative 5% growth assumption to 4.5%. A spending adjustment of +1 percentage point of GDP changes an illustrative expenditure ratio of 20% to 21% of GDP.

Transfers and FDI follow the workbook's negative-inflow convention. Check the sign against the intended inflow change. Asset adjustments use currency amounts at the workbook's scale, so entering 1 can mean one million or one billion local-currency units. Read the displayed unit first. Positive/negative colors describe the input's sign, not whether an outcome is desirable.

**Start a new scenario** sets every adjustment to zero. **Use the workbook’s existing customized scenario** preserves the supplied adjustment paths. Loading an illustrative case creates a new editable draft with the assumptions stated by that exercise. Period entry changes only the inclusive selected years; the complete annual editor exposes the rest.

## Set external financing terms

With **Set new financing terms for this scenario** unchecked, the app retains the supplied values and formulas in `Customized Scenario-External`. Checking it replaces all three supported financing terms:

| Field | Workbook cell | Browser entry | JSON storage |
| --- | --- | --- | --- |
| Interest rate | C21 | Level in percent, e.g. `4` for 4% | Decimal, e.g. `0.04` |
| Grace period | C23 | Whole years, zero or greater | `grace_years` |
| Maturity | C24 | Whole years, greater than grace | `maturity_years` |

The rate must be nonnegative. The controls concern the supported new external financing assumption. They do not reset interest on the whole debt stock or change the framework discount rate. Financing effects depend on the workbook's relevant new borrowing needs. Inherited formulas and an explicit override at today's supplied values may behave differently as other inputs change.

## Read the supported results

Present value (PV) and public and publicly guaranteed (PPG) debt use the workbook's definitions. Results contain the following six indicators. Every observation retains its source cells, year, units, reference baseline, as-supplied customized value and saved-scenario value.

| JSON metric | Indicator | Units |
| --- | --- | --- |
| `ext_pv_gdp` | PV of PPG external debt / GDP | Percent of GDP |
| `ext_pv_exports` | PV of PPG external debt / exports | Percent of exports |
| `ext_ds_exports` | PPG external debt service / exports | Percent of exports |
| `ext_ds_revenue` | PPG external debt service / revenue | Percent of revenue |
| `public_pv_gdp` | PV of total public debt / GDP | Percent of GDP |
| `public_pv_revenue` | PV of total public debt / revenue | Percent of revenue |

Each indicator is reported at offsets **0, 2, 5, 10, 15 and 20** from the first projection year: years 1, 3, 6, 11, 16 and 21 of the horizon. That gives 36 observations per scenario. The exact public example reports 2024, 2026, 2029, 2034, 2039 and 2044. Other supported workbooks use their own first projection year.

The four external thresholds and total-public-debt PV/GDP benchmark come from recognized `CI Summary` cells. There is no supported threshold for public PV/revenue. Missing thresholds are stated as unavailable. Missing/error observations stay missing/error values, never zero.

Difference columns subtract the selected saved-case comparator from the scenario, in percentage points. For example, 45% of GDP minus 42% of GDP equals +3 percentage points. Keep the comparator distinct from the separately displayed reference baseline.

The tool does not deliver the complete official stress-test suite, public debt service/revenue, annual output series, an official risk rating, estimated investment returns or an upstream-model connection. Annual input editing does not expand output coverage. Do not infer annual peaks or first crossings between samples.

## Choose an output file

| Output | Contains | Use |
| --- | --- | --- |
| Standard PNG | Six-panel overview | Quick review of sampled debt paths and thresholds |
| Policy PNG | Six-panel comparison overview | Explain levels and differences at labelled sampled years |
| Either PDF | Overview, six indicator pages, shared-explanation annex | Readable briefing with the assumptions' rationale |
| Comparison JSON v3 | Definitions, years, full-precision results, identities, evidence and shared explanations | Inspect or process the numerical record |
| Stopped workspace backup | Workbook copies, saved revisions, journals, results and jobs | Private recovery, using a compatible runtime |

There is no spreadsheet-export control or scenario-file re-import workflow in this version. JSON and chart exports are distinct from full workspace recovery. See [exchange and recovery](exchange-recovery.md).
