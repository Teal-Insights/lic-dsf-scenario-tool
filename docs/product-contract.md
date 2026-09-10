# General product contract

The product accepts a completed supported LIC-DSF IDA21 workbook, checks it, and enables the analyst to enter the 13 customized-scenario macro paths and external financing terms. Input labels, units and fiscal-year mapping follow the template. Period entry and year-by-year entry should be easy to understand; blank and explicit zero remain distinct.

The baseline belongs to the uploaded workbook. Example data are an optional, explicitly illustrative route. Results, saved scenarios, reasoning and exports bind to exact workbook and assumption identities. Do not combine cases from different baselines under one unqualified comparison.

The application must preserve original files, report unsupported structures specifically, retain previous valid results after failures, and refuse ambiguous stale-result exports. A successful calculation with pending exact-run evidence is useful but must remain visibly distinct from an Excel-verified result. Numerical checks retain `atol=1e-6`, error-class equality and first-divergence reporting.

The interface should have a descriptive title, a prominent work-in-progress notice, numbered next actions and concise contextual help. It must explain that the scenario inputs correspond to the template's customized-scenario tabs, and explain the scope of financing controls. Branding must not displace the analyst's task.

Two chart views are required: familiar **Standard LIC-DSF** charts for framework users and polished **Policy briefing** charts for communicating supported takeaways to senior policymakers. Both use the same results and preserve evidence, units, years and comparator. See the [chart-view contract](chart-views.md); this is a substantive audience-specific visualization requirement, not just a color theme.

The public release requires a reproducible installation route, an independently tested tutorial, methods and compatibility documentation, input/output schemas, recovery instructions, accessible chart alternatives, clear licenses and privacy documentation. The application must not require a maintainer's machine, private file paths or a confidential sample to run.

Local processing, offline behavior, supported platforms, numerical coverage, export privacy and accessibility each require evidence from the actual release. Do not substitute successful development-machine execution for these checks. Design alignment with a standard is not formal recognition.
