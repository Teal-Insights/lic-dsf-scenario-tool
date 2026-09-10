# Methods, compatibility and evidence

The tool exposes a bounded part of the English LIC-DSF IDA21 workbook. It evaluates workbook formulas with a pinned Python evaluator and a version-specific semantic adapter. It does not introduce a separately calibrated economic model, run VBA, refresh external links or use Excel as its calculation runtime.

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

Enter additions to the workbook's customized levels, not replacement levels. Transfers and FDI use the template's negative-inflow convention; inspect the intended sign. A UI blank is invalid, while explicit zero is no adjustment. At intake only, recognised literal empty delta cells may become zero where their level formula directly adds that cell. Formula inputs without saved values are not literal blanks and are not silently zeroed.

An unchecked financing override retains the workbook's supplied financing values and formulas. An override requires all three terms: interest rate as a decimal, whole-year grace, and whole-year maturity greater than grace. Rate and grace must be nonnegative. These are external financing assumptions, not the framework discount rate.

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

Revisions bind the workbook, full scenario definition and definition hash. Runs retain their original result, engine identity, contract version and result hash. Current-result retrieval rejects a different revision, definition or runtime. A later calculation cannot attach itself to inputs edited while it ran.

The JSON export uses `lic-dsf-comparison-v1`: workbook identity, selected comparator, labelled runs, revisions, hashes, scenario inputs, year mapping, source-cell points, thresholds and evidence. Private reasoning is excluded. JSON is a portable record; this preview does not provide a JSON re-import workflow or guarantee schema migration across future versions.
