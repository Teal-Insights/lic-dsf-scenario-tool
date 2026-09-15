# General product contract

The product accepts a completed supported LIC-DSF IDA21 workbook, checks it, and enables the analyst to enter the 13 customized-scenario macro paths and external financing terms. Input labels, units and fiscal-year mapping follow the template. Period entry and year-by-year entry should be easy to understand; blank and explicit zero remain distinct.

The baseline belongs to the selected workbook. Example data are an optional, explicitly illustrative route. Results, saved scenarios, reasoning and exports bind to exact workbook and assumption identities. Do not combine cases from different baselines under one unqualified comparison.

The application must preserve original files, report unsupported structures specifically, retain previous valid results after failures, and refuse ambiguous stale-result exports. A successful calculation with pending exact-run evidence is useful but must remain visibly distinct from an Excel-verified result. Numerical checks retain `atol=1e-6`, error-class equality and first-divergence reporting.

The interface should have a descriptive title, a prominent work-in-progress notice, numbered next actions and concise contextual help. It must explain that the scenario inputs correspond to the template's customized-scenario tabs, and explain the scope of financing controls. Branding must not displace the analyst's task.

Two chart views are required: familiar **Standard LIC-DSF** charts for framework users and polished **Policy briefing** charts for communicating supported takeaways to senior policymakers. Both use the same results and preserve evidence, units, years and comparator. See the [chart-view contract](chart-views.md); this is a substantive audience-specific visualization requirement, not just a color theme.

The public release requires a reproducible installation route, an independently tested tutorial, methods and compatibility documentation, input/output schemas, recovery instructions, accessible chart alternatives, clear licenses and privacy documentation. The application must not require a maintainer's machine, private file paths or a confidential sample to run.

Local processing, offline behavior, supported platforms, numerical coverage, export privacy and accessibility each require evidence from the actual release. Do not substitute successful development-machine execution for these checks. Design alignment with a standard is not formal recognition.

Deliberately shared explanations belong to scenario revisions and accompany PDF/data exports. Keep them separate from private journals; an upgrade must never share existing private notes automatically. Generic learning exercises must expose their complete assumptions and matched controls.

Briefing labels and their connector lines must remain legible without overprinting. PDF explanation headings must stay with their body text, and a continued explanation must identify its driver on the next page.

## Visible analyst workflow

The selected input has an editable 21-year path, nearby expandable help and a shared explanation field. Direction colors also use text/sign cues and remain distinct from unsaved-edit markers. Blank values are unfinished, not zero. A complete-grid view and changed-input summary support review. The five steps distinguish loaded, manually reviewed, saved, calculated, compared and download-prepared states; none implies fresh Excel verification.

A current calculation/comparison loads Standard LIC-DSF and Policy briefing previews together. Full-width charts are the default; side-by-side layout is available only on wide screens. Each view has explicitly labelled PDF/PNG downloads. Both images are accepted only for one unchanged comparison. Changing numerical inputs, source or selection clears both. The chart heading and the legend labels of the selected cases are edited in one **Chart text** panel beside the previews. Editing them retains the previews with their saved text and pauses comparison and downloads. **Apply to both views** or **Discard edits and keep saved text** refreshes both views automatically when the selected calculations are current and numerical inputs are unchanged; neither action recalculates the scenarios. A saved revision that changes only a case's name, legend label or shared explanations keeps its current calculation; only changed inputs or financing terms require a new calculation. Summaries of every selected alternative accompany the chosen indicator; full reported-year summaries also appear in both PDFs. The numerical engine, its selected-year output coverage, tolerances and sharing boundaries are unchanged. See the updated tutorial for the complete workflow.

## Reuse prepared assumptions

A single scenario file must carry only its version, exact workbook fingerprint, projection years, complete numerical definition, shared label and shared explanations. Download uses the saved current revision after server readback; no workbook, private journal, internal name, chart heading, results or evidence is included. Review intentionally shared text and assumptions before sending the file.

Import requires the exact workbook and years and creates a new unsaved draft without overwriting saved cases. Its shared label initially supplies the workspace name and chart label. The analyst reviews, saves and calculates it; import never establishes verified results. Reject unsupported fields/versions, incomplete or nonfinite paths, invalid terms/text and files larger than 131,072 bytes. Cross-workbook translation, year remapping, upstream-model translation, bulk case sets and comparison-JSON import are outside this contract. See [scenario-file details](data-contract.md#scenario-files).


## Comparison clarity and reopening

Reopen a saved workbook in step 1 to retrieve its scenarios. The interface distinguishes a workbook that has not been selected from a selected workbook without saved cases. Scenario-label counters refresh when a draft or saved case opens.

The workbook reference baseline and a calculated customized scenario can differ even with zero macro adjustments. Choose a comparison case that isolates the assumptions being examined, and review macroeconomic paths and financing terms together. A reference-to-control difference is not itself a policy effect. This reminder is visible beside the chart previews. Standard-view lines may overlap when differences are small; the policy view shows differences explicitly.

Policy detail charts show differences from the selected comparison case across every reported year, with a zero line and explicit percentage-point units. Standard charts retain levels and thresholds. Neutral policy titles do not pick a winning case. Summaries cover every selected alternative: latest comparable value, reported minimum and maximum difference, sign changes and missing coverage. They do not infer annual peaks or causal benefits. Summaries and policy labels distinguish exact zero (0.00) from nonzero differences below 0.005 pp (≈0.00). Values use two decimals, or scientific notation for magnitudes of 10²¹ or more. The ordinary table rounds small differences; CSV/JSON retain full precision.


## Portable charts and complete briefing packet

The interface uses locally bundled IBM Plex Serif and Inter under the SIL Open Font License. No remote font service or extra user installation is required. Both chart styles show one selected indicator as a crisp SVG; choose another indicator to update both together. The standard overview remains available in the PDF report. The underlying observations, comparison and evidence are identical. Chart lines join only the supported reported years.

Download briefing packet (.zip) produces both PDF reports, twelve individual PNG and twelve vector SVG charts, five CSV tables, an Excel workbook with the same tables, full-precision comparison JSON and a SHA-256 file manifest. Tables include results, annual macro adjustments, financing terms, shared explanations and evidence. They carry the workbook identity and verification status. CSV/JSON numbers are not presentation-rounded; Excel retains its native numeric precision. Blank observations stay missing and calculation error strings remain text. CSV user text beginning with a formula character receives a protective apostrophe; the JSON preserves original text.

The packet is built from one current saved comparison, using the same export field selection as existing JSON. It excludes the original workbook, private journal and internal workspace names. Shared explanations can contain sensitive information: inspect the packet before sharing. It is not a backup or an importable scenario file.


## Readable guidance and evidence

Both PDF reports now begin with a reading guide, and Excel opens a **Read me first** sheet. These explain purpose, source, assumptions, comparison, check limits and file fingerprints before technical detail. CSV/JSON schemas and exact numerical values are unchanged. See [reading and sharing a briefing](reading-briefing.md).

Contextual help must explain an unfamiliar term at its point of use. Progress distinguishes missing calculations from missing selection. Input summaries may show rounded, abbreviated paths while exact edits and exports remain unchanged; small nonzero values must not appear as literal zero. No automated economic-realism assessment or official endorsement is implied.


## Built-in illustrative learning route

A first-time user can start the official example without a file chooser, and load complete illustrative investment cases without importing scenario files. The app downloads the exact publisher workbook on explicit action, verifies its fingerprint and retains a local copy for offline reuse. It does not bundle or relicense the workbook. First-use network behavior is disclosed beside the action; private workbook and scenario data are not included in the download request.

The three prepared cases bind to the exact official workbook and projection years: No investment, Larger assumed benefit and Smaller assumed benefit. Their external financing assumptions match at 8% interest, 4-year grace and 9-year maturity. Load creates an unsaved draft; review, save and calculate remain explicit. Loading must not overwrite saved cases or silently discard drafts. The user chooses No investment as comparator. Shared explanations identify the coordinated fiscal/growth paths and illustrative assumptions, without a promise of returns or independent calibration.

This optional learning route supplements own-workbook intake. Generic sensitivity exercises and advanced scenario-file exchange remain available. It does not expand supported workbook versions or numerical coverage, establish fresh Excel verification, or turn the general tool into an investment-specific product. This reconciled candidate requires fresh source checks and independent artifact review. Final release artifacts, installation and representative offline/connected network observation must be documented separately.
