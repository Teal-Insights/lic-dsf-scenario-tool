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
