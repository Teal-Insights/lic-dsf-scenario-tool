# Methods, compatibility and evidence

The tool exposes a bounded part of the English LIC-DSF IDA21 workbook. It evaluates workbook formulas with a pinned Python evaluator and a version-specific semantic adapter. It does not introduce a separately calibrated economic model, run VBA, refresh external links or use Excel as its calculation runtime.

[Documentation index](README.md) · [Full input/output reference](workbooks-inputs-outputs.md) · [Worked exercise](tutorial.md)

## Inputs and signs

All 13 paths contain 21 explicit finite numeric adjustments. Their labels and workbook-year mapping are checked at intake. Period entry fills the chosen inclusive range; year-by-year entry exposes the complete horizon.

| Customized input | Adjustment units |
| --- | --- |
| Revenue and grants; primary expenditure; grants | Percentage points of GDP |
| Public sector assets | Local currency, at the workbook's scale |
| Real GDP growth; GDP deflator inflation; nominal depreciation | Percentage points |
| Exports; imports | Percentage points of GDP |
| Official current transfers; private current transfers; net foreign direct investment | Percentage points of GDP |
| GDP deflator in US dollars | Percentage points |

The saved delta paths replace the workbook's delta-cell entries for the selected scenario. The template's level formulas then add those adjustments to their underlying assumptions. They do not stack an additional delta on top of a previously supplied delta. Transfers and FDI use the template's negative-inflow convention; inspect the intended sign. A UI blank is invalid, while explicit zero is no adjustment. At intake only, recognised literal empty delta cells may become zero where their level formula directly adds that cell. Formula inputs without saved values are not literal blanks and are not silently zeroed.

An unchecked financing override retains the workbook's supplied financing values and formulas. An override requires all three terms: interest rate entered as a percent in the interface (4 means 4%, stored as decimal 0.04), whole-year grace, and whole-year maturity greater than grace. Rate and grace must be nonnegative. These are external financing assumptions, not the framework discount rate.

## Three different numerical channels

| Channel | Meaning |
| --- | --- |
| Reference baseline | The workbook's actual Baseline output rows |
| As supplied customized | Customized output calculated using the workbook's supplied inputs |
| Scenario | Customized output calculated using the saved scenario's adjustments and financing choice |

An imported case preserves existing adjustments. A zero-adjustment case contains all explicit zero paths. Neither should be silently renamed the reference baseline. Every comparison uses one workbook identity and explicitly names a selected saved-case comparator.

## Outputs and chart coverage

The result contains 36 metric-year points: external public and publicly guaranteed debt PV/GDP, PV/exports, service/exports and service/revenue; total public debt PV/GDP and PV/revenue. Observations occur at projection offsets 0, 2, 5, 10, 15 and 20. Inputs nevertheless span all 21 years.

Ratios retain their percent-of-denominator units. Scenario-minus-comparator differences are percentage points. Each point records source cells. Thresholds and the public-debt benchmark come from supported CI Summary cells. No supported threshold is provided for public PV/revenue. Missing values and recognised spreadsheet errors remain missing/error observations; they are never economic zeros.

Historical and tailored stress tests, public debt service/revenue, all annual outputs and a complete official risk classification are outside this output set. Lines between sampled points are visual guides, not interpolated annual values. Do not infer a first crossing, annual peak, causal attribution or policy recommendation from them.

## Read evidence as separate claims

| Evidence | What it establishes | What it does not establish |
| --- | --- | --- |
| SHA-256 identity | Exact workbook bytes | Compatibility or correctness |
| Supported structure | Recognised sheets, labels, years and formula geometry | Support for arbitrary formula edits |
| Saved-cache agreement | Selected evaluator outputs agree with values saved in the supplied file | Fresh Excel recalculation |
| Dynamic-reference/output checks | Reports observed changes in selected sentinels, missing/error outputs or reference baselines | A no-trigger result does not prove the absence of missed dependencies, including within or outside the monitored set |
| Computed, unverified | The current saved inputs produced a result with stated checks | Exact-run Excel equivalence |
| Review required | A reported inconsistency needs investigation | Permission to treat the result as verified |
| Exact Excel comparison | Only the exact workbook, inputs, engine and probes covered by its receipt | Other revisions, machines, formulas or unsupported outputs |

Fresh Excel acceptance is not established for this preview. Hash and sentinel checks must not be presented as substitutes. A valid numerical check retains absolute tolerance `1e-6`, exact error-class comparison and first-divergence reporting; coverage must name the actual probes.

## Saved records and portability

Revisions bind the workbook, full scenario definition and definition hash. Runs retain their original result, engine identity, contract version and result hash. A saved revision that changes only the name, legend label or shared explanations can reuse an already-current calculation from the uninterrupted sequence of revisions with the same numerical definition. The exported revision and shared text reflect the current saved revision; the original numerical result and result hash remain unchanged. Changed inputs, financing terms, workbook or runtime identity require a matching calculation. Returning to an earlier definition after an intervening numerical edit still requires calculation. A text-only save cannot make an absent or stale result current, and a calculation cannot be presented as the result of different numerical inputs.

New JSON exports use `lic-dsf-comparison-v3`: workbook identity, selected comparator, labelled runs, revisions, hashes, scenario inputs, year mapping, source-cell points, thresholds, evidence and the explicit chart-context label/revision. The version-1 schema remains available for historical exports. Deliberately shared per-input explanations are included; private journals are excluded. JSON is a portable record; this preview does not provide a JSON re-import workflow or guarantee schema migration across future versions.

The learning examples supply assumptions, not estimated policy effects: growth ±1 percentage point in years 1–3, funding rate ±1 percentage point around a matched supplied-rate control, and investment spending +1 point of GDP in years 1–3 with an optional assumed growth benefit of +0.25 points in years 4–8. Compare with the indicated control; funding may show no effect without relevant new financing needs.
