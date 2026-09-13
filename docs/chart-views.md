# Two chart views, one numerical record

Both chart views are required product features. They must use the same saved calculations, workbook and scenario identities, fiscal years, units, comparator and evidence status. Changing the view must not recalculate or change economic results.

## Standard LIC-DSF charts

Provide the recognizable chart structure used in IMF/World Bank LIC-DSF outputs. Inspect the supported official template's actual chart references before implementation. Preserve familiar indicator naming, panel arrangement, baseline/scenario distinction and threshold or benchmark conventions for the supported output set. Clearly identify any difference in coverage from the workbook's full output. Familiar styling is not a claim of institutional endorsement or an official risk rating.

## Policy briefing charts

Provide a polished communication view for senior policymakers using data-visualization best practices. Make the supported policy-relevant comparison clear through visual hierarchy, direct labels, deliberate emphasis, accessible color and non-color cues, restrained annotation and suitable chart geometry. Use concise sentence headlines only when the exact data and selected comparison support them.

Retain metric definitions, units, years, comparator and material limitations. Do not invent causal attribution, uncertainty bands, annual values, peaks or first-crossing dates. When zooming a scale or simplifying a view, make the choice clear and preserve access to the reference chart and numerical table. Analyst interpretation remains distinct from a calculated difference.

## Interface, export and acceptance

Use explicit view names: **Standard LIC-DSF** and **Policy briefing**. Both must be available in the app and export workflow. Exports identify the view and retain the same underlying record and evidence context. Preserve accessible numeric tables and explicit sharing scope in both.

Acceptance requires: traceability to the same full-precision values; inspection against actual standard-template chart references; independent review of the policy view's interpretation and visual design; readable actual PDF/PNG outputs without clipped labels; and verification that switching views or exporting cannot alter the scenario, comparator, numbers or verification status.

The two views must be documented with examples and guidance on audience and use. The current local application implements both views. This page records their design and acceptance requirements; [the chart guide](charts.md) describes the actual output and its limits. Version-specific test evidence remains separate from this requirement.


## Comparison clarity and reopening

Reopen a saved workbook in step 1 to retrieve its scenarios. The interface distinguishes a workbook that has not been selected from a selected workbook without saved cases. Scenario-label counters refresh when a draft or saved case opens.

The workbook reference baseline and a calculated customized scenario can differ even with zero macro adjustments. Choose a comparison case that isolates the assumptions being examined, and review macroeconomic paths and financing terms together. A reference-to-control difference is not itself a policy effect. This reminder is visible beside the chart previews. Standard-view lines may overlap when differences are small; the policy view shows differences explicitly.

Policy detail charts show differences from the selected comparison case across every reported year, with a zero line and explicit percentage-point units. Standard charts retain levels and thresholds. Neutral policy titles do not pick a winning case. Summaries cover every selected alternative: latest comparable value, reported minimum and maximum difference, sign changes and missing coverage. They do not infer annual peaks or causal benefits. Summaries and policy labels distinguish exact zero (0.00) from nonzero differences below 0.005 pp (≈0.00). Values use two decimals, or scientific notation for magnitudes of 10²¹ or more. The ordinary table rounds small differences; CSV/JSON retain full precision.


## Portable charts and complete briefing packet

The interface uses locally bundled IBM Plex Serif and Inter under the SIL Open Font License. No remote font service or extra user installation is required. Both chart styles show one selected indicator as a crisp SVG; choose another indicator to update both together. The standard overview remains available in the PDF report. The underlying observations, comparison and evidence are identical. Chart lines join only the supported reported years.

Download briefing packet (.zip) produces both PDF reports, twelve individual PNG and twelve vector SVG charts, five CSV tables, an Excel workbook with the same tables, full-precision comparison JSON and a SHA-256 file manifest. Tables include results, annual macro adjustments, financing terms, shared explanations and evidence. They carry the workbook identity and verification status. CSV/JSON numbers are not presentation-rounded; Excel retains its native numeric precision. Blank observations stay missing and calculation error strings remain text. CSV user text beginning with a formula character receives a protective apostrophe; the JSON preserves original text.

The packet is built from one current saved comparison, using the same export field selection as existing JSON. It excludes the original workbook, private journal and internal workspace names. Shared explanations can contain sensitive information: inspect the packet before sharing. It is not a backup or an importable scenario file.
