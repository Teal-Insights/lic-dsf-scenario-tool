# General product contract

The product accepts a completed supported LIC-DSF IDA21 workbook, checks it, and enables the analyst to enter the 13 customized-scenario macro paths and external financing terms. Input labels, units and fiscal-year mapping follow the template. Period entry and year-by-year entry should be easy to understand; blank and explicit zero remain distinct.

The baseline belongs to the uploaded workbook. Example data are an optional, explicitly illustrative route. Results, saved scenarios, reasoning and exports bind to exact workbook and assumption identities. Do not combine cases from different baselines under one unqualified comparison.

The application must preserve original files, report unsupported structures specifically, retain previous valid results after failures, and refuse ambiguous stale-result exports. A successful calculation with pending exact-run evidence is useful but must remain visibly distinct from an Excel-verified result. Numerical checks retain `atol=1e-6`, error-class equality and first-divergence reporting.

The interface should have a descriptive title, a prominent work-in-progress notice, numbered next actions and concise contextual help. It must explain that the scenario inputs correspond to the template's customized-scenario tabs, and explain the scope of financing controls. Branding must not displace the analyst's task.

Two chart views are required: familiar **Standard LIC-DSF** charts for framework users and polished **Policy briefing** charts for communicating supported takeaways to senior policymakers. Both use the same results and preserve evidence, units, years and comparator. See the [chart-view contract](chart-views.md); this is a substantive audience-specific visualization requirement, not just a color theme.

The public release requires a reproducible installation route, an independently tested tutorial, methods and compatibility documentation, input/output schemas, recovery instructions, accessible chart alternatives, clear licenses and privacy documentation. The application must not require a maintainer's machine, private file paths or a confidential sample to run.

Local processing, offline behavior, supported platforms, numerical coverage, export privacy and accessibility each require evidence from the actual release. Do not substitute successful development-machine execution for these checks. Design alignment with a standard is not formal recognition.

Deliberately shared explanations belong to scenario revisions and accompany PDF/data exports. Keep them separate from private journals; an upgrade must never share existing private notes automatically. Generic learning exercises must expose their complete assumptions and matched controls.

## Visible analyst workflow

The selected input has an editable 21-year path, nearby expandable help and a shared explanation field. Direction colors also use text/sign cues and remain distinct from unsaved-edit markers. Blank values are unfinished, not zero. A complete-grid view and changed-input summary support review. The five steps distinguish loaded, manually reviewed, saved, calculated, compared and download-prepared states; none implies fresh Excel verification.

A current calculation/comparison loads Standard LIC-DSF and Policy briefing previews together. Full-width charts are the default; both remain available in a side-by-side layout. Each view has explicitly labelled PDF/PNG downloads. Both images are accepted only for one unchanged comparison. Changing numerical inputs, source or selection clears both. The chart heading and the legend labels of the selected cases are edited in one **Chart text** panel beside the previews. Editing them retains the previews with their saved text and pauses comparison and downloads. **Apply to both views** or **Discard edits and keep saved text** refreshes both views automatically when the selected calculations are current and numerical inputs are unchanged; neither action recalculates the scenarios. A saved revision that changes only a case's name, legend label or shared explanations keeps its current calculation; only changed inputs or financing terms require a new calculation. Text takeaways, one per indicator and derived by the same rule as the policy headlines, accompany the previews. The numerical engine, its selected-year output coverage, tolerances and sharing boundaries are unchanged. See the updated tutorial for the complete workflow.
