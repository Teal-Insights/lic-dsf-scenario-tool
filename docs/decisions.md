# Recorded product decisions

Accepted product direction, 9 September 2026. Changes require a dated record explaining what supersedes the earlier decision; a restricted demonstration does not silently change the general product contract.

| ID | Decision | Status |
|---|---|---|
| G-001 | General-purpose, upload-first LIC-DSF scenario analysis over the template's own customized-scenario mechanism | Accepted |
| G-002 | Public repository, MIT software license and independently usable documentation | Required for release |
| G-003 | Public source and history contain general software and reviewed public documentation only | Mandatory |
| G-004 | Official World Bank published IDA21 template is the reference input; embedded Ghana-labelled data are illustrative | Accepted |
| G-005 | Supported uploads may calculate and export with explicit pending exact-Excel-verification labels | Accepted |
| G-006 | Hash identity, structural compatibility and numerical verification remain distinct | Accepted |
| G-007 | Work-in-progress notice, descriptive product title and numbered steps; modest maintainer attribution in footer | Accepted |
| G-008 | Saved scenarios, comparator, cumulative reasoning and explicit sharing scope are core features | Accepted |
| G-009 | Design against the Digital Public Goods Standard; formal recognition and legal/rights conclusions require their own evidence | Accepted |
| G-010 | Original workbooks and prior results remain recoverable; changed inputs invalidate current-result status | Accepted |
| G-011 | Two chart views: familiar Standard LIC-DSF and polished Policy briefing; one shared numerical/evidence record | Required in app and exports |

Implementation choices still requiring evidence include exact supported workbook layouts, treatment of populated customized-scenario cells, compatibility diagnostics, installation and platform acceptance. They must not be concealed behind an upload button or inferred solely from a template filename.

Implementation clarification, 9 September 2026: outward chart context is an optional label explicitly saved for the full workbook identity, with an independent revision. It never defaults from internal filenames, scenario names or private journals. New comparison exports use v2, preserving v1 reading and the existing numerical contract. Every rendered chart page retains evidence and a visible source-hash reference; neither the label nor the hash upgrades a verification claim.

## Analyst journey clarification

Use familiar projection-year language, visible illustrative learning examples and a purpose/scope explanation linked to the methodology. Put the shared chart-context label beside chart controls. Keep file identity and verification details accessible without making them the primary baseline view. Percentage-point adjustments step by 0.1, with typed precision; financing rate entry uses percent and converts once to the canonical decimal representation. Preserve untouched supplied rate precision. These presentation changes do not expand numerical coverage, add scenario-file import, or convert private journals into shared rationale.

## 10 September: generic exercises and shared explanations

Three illustrative exercise families use the loaded workbook’s years and supplied financing terms. Growth and funding have matched center cases; investment has a cost-only control and an explicitly assumed later growth benefit. All paths are visible and editable, with unsupported negative funding rates refused rather than clamped. No example is a calibrated recommendation.

New deliberately shared explanations are optional per driver and financing path, saved with scenario revisions and included in comparison-v3 JSON and PDF annexes. Missing explanations for adjusted drivers remain explicit. Existing private journals remain private. Additive workspace schema 3 migration does not rewrite earlier numerical records or promote private text. At this decision date, scenario-file import and annual-output expansion were separate pending work. The 11 September scenario-file decision below supersedes the import status only.

## Visible analyst workflow

The selected input has an editable 21-year path, nearby expandable help and a shared explanation field. Direction colors also use text/sign cues and remain distinct from unsaved-edit markers. Blank values are unfinished, not zero. A complete-grid view and changed-input summary support review. The five steps distinguish loaded, manually reviewed, saved, calculated, compared and download-prepared states; none implies fresh Excel verification.

A current calculation/comparison loads Standard LIC-DSF and Policy briefing previews together. Full-width charts are the default; side-by-side layout is available only on wide screens. Each view has explicitly labelled PDF/PNG downloads. Both images are accepted only for one unchanged comparison. Changing numerical inputs, source or selection clears both. The chart heading and the legend labels of the selected cases are edited in one **Chart text** panel beside the previews. Editing them retains the previews with their saved text and pauses comparison and downloads. **Apply to both views** or **Discard edits and keep saved text** refreshes both views automatically when the selected calculations are current and numerical inputs are unchanged; neither action recalculates the scenarios. A saved revision that changes only a case's name, legend label or shared explanations keeps its current calculation; only changed inputs or financing terms require a new calculation. Summaries of every selected alternative accompany the chosen indicator; full reported-year summaries also appear in both PDFs. The numerical engine, its selected-year output coverage, tolerances and sharing boundaries are unchanged. See the updated tutorial for the complete workflow.

## Documentation clarification

The row identifiers, units, year mapping and output coverage are consolidated in the [input/output reference](workbooks-inputs-outputs.md). [The tutorial](tutorial.md) uses only the separately supplied official illustrative workbook. Annual output expansion and hosted calculation remain pending. [Exchange and recovery](exchange-recovery.md) distinguishes scenario input files, comparison results and private workspace backups; the 11 September scenario-file decision below defines the supported exchange scope.

## 11 September: round 002 design slice (Claude Code implementation, independently reviewed)

Outward chart text is edited beside the previews: one **Chart text** panel in step 5 holds the heading and one legend label per selected case, with counters and a shared apply/discard pair. A legend change saves a new revision of the case; a revision that changes only the name, legend label or shared explanations keeps the calculation of the revision it was saved from (`store._numerical_base_revision`), while any change to inputs or financing terms, including a restore after an intervening change, still requires calculation. The exported `revision` is the current saved revision and `result_hash` still identifies the unchanged result.

State copy was made truthful: the step navigation no longer points backwards after a comparison, a draft edit that clears previews says so, a stale heading from another tab is reloaded automatically (or the draft is kept and the recovery button named), a single case compared with itself is flagged, and a chart render failure names the fix. Input safety: typographic minus signs pasted into number fields are converted or leave the field unfinished instead of flipping the sign; blank-year errors focus the visible year box; financing terms are checked before save; the scenario name is required; legend labels are checked for emptiness, duplicates, paths and the reserved “Reference baseline” at save time; intake refusals are plain sentences.

Presentation: colours mean the same in both chart views (baseline navy, emphasised case cyan, comparator gray); the standard overview has one legend and labelled threshold lines; the analyst's heading is the page title with the view name as a kicker; policy headlines name the comparator and the unit (“Lower growth is 1.1 pp of GDP above Growth control in 2044”) and the app lists the same sentences as text takeaways; negative numbers use a typographic minus; the sampled-points caveat is printed once per page; annex driver labels are bold. Download names are `scenario-comparison-standard`, `scenario-comparison-policy` and `scenario-comparison-data.json`. Indicator names on screen match the exports. The comparison table shows two decimals and no difference column for the comparator.

Deferred with reasons: connector length in the policy overview (a relative-difference encoding would change the chart's meaning; decision requested), one paper size for all PDF pages (layout risk for long headings; separate slice), keeping previews on screen while a draft is dirty (conflicts with the “changing inputs clears both” contract; decision requested), a revisions list and restore, and a glyph check at heading apply time.

### 11 September, corrections after Codex review (R2-CX-01 to R2-CX-04)

Legend labels and the heading are applied through one atomic store operation (`ScenarioStore.save_chart_text`, route `/api/chart-text`): all values validated first, all expected revisions checked in one `BEGIN IMMEDIATE` transaction, complete rollback on any refusal, and the final label set validated as a whole so swaps are accepted and duplicates refused. After any chart-text apply, discard or automatic conflict reload, the open case is reloaded as one coherent editor snapshot (inputs, financing terms, explanations, revision, result state) with an unsaved journal draft preserved; a new revision token is never combined with older editor inputs. The inline calculation status beside the Calculate button is derived from the actual state on every exit path (refused start, failed or interrupted job, review-required result, a newer draft during the run). No engine, evidence, tolerance or privacy behavior changed.

## 11 September: single-scenario file exchange

One `lic-dsf-scenario-v1` file carries a complete numerical definition, exact workbook SHA-256 and projection years, shared label and shared explanations. Download selects these fields from the saved revision after server readback. It excludes the workbook, results, evidence, private journal, internal name and chart heading.

Import requires the exact loaded workbook and year sequence and opens a new unsaved draft. The shared label becomes its initial workspace name and chart label; review, save and calculate remain explicit steps. Saved cases are never overwritten by import. Unsupported fields/versions, invalid paths, financing or text, and files above 131,072 bytes are refused. Comparison-v3 results remain a different, non-importable format.

This supersedes earlier statements that all scenario-file import is pending. Cross-workbook translation, year remapping, upstream-model translation and multi-case sets remain outside this exchange contract. Numerical coverage, verification rules and full-workspace recovery are unchanged.

## 12 September: readable chart callouts and explanation continuations

Policy chart endpoint leaders stay to the left of the label column and below the text layer. Each label retains its actual observed year and value. PDF annexes keep driver headings with the first explanation lines and repeat the driver heading with a continuation marker when an explanation spans pages. These are renderer changes; numerical definitions, calculations, evidence and sharing fields are unchanged. Existing result identities remain bound to the code version that produced them; renderer validation alone does not establish acceptance of calculations under a newer application identity.


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


## 12 September: general-purpose comparison corrections

This supersedes the earlier first-alternative/latest-year headline rule. No use case receives an automatic causal story. Policy detail charts plot differences over all reported years. Every alternative receives a summary of the latest comparable observation, reported range, sign changes and missing coverage. The PDF snapshot uses the last reported year consistently, retaining missing values rather than silently switching the entire panel to an earlier year. Case colours and markers are shared across views, with alternatives sorted by shared label. Both PDFs include the all-indicator summaries. Numerical CSV/JSON contracts remain unchanged.

Table links open and focus the numerical table below the sticky status bar. Tables retain native scrolling and keyboard access. The active editor names its case and revision. A saved-input comparison distinguishes changed macro paths from financing treatment. Full-width charts remain the default and narrow screens cannot switch to unreadably small side-by-side panels. The 2024 references are explicitly identified as climate-section guidance; application to general scenario analysis is an interpretation.


## 13 September: experimental release, documentation and contributions

The first downloadable preview supports an explicit Windows and Mac distribution plan with architecture-specific evidence and honest signing status. Documentation should combine approachable worked guides with a useful code reference. Describe iterative development and welcome stakeholder co-design without implying endorsement. Provide a forwardable institutional IT information page without a blanket ask-IT-first onboarding step. Welcome contributions subject to maintainer roadmap control, contributor accountability, meaningful review and secure release controls.


## 13 September: DPG evidence and practical design choices

Maintain the earlier indicator-by-indicator DPG assessment, updating evidence as capabilities change. The standard informs good practices and iterative stakeholder co-design; no certification, formal recognition or full-compliance claim is made. Evaluate consequential technical requirements against stakeholder needs, privacy, security, accessibility and maintenance costs without assuming a conflict. Record unmet or uncertain criteria honestly. Formal nomination remains optional, and actual confidentiality, rights or analytical defects still require correction or a narrower offered scope.


## 13 September: locale-independent calculation files

Calculation requests, results and errors use explicit UTF-8 encoding at both ends of the worker boundary. An isolated Windows interpreter may ignore Python encoding environment variables, so a non-English workbook path must not depend on the operating-system locale. A subprocess regression reproduces the prior failure under a non-UTF-8 default. This changes file encoding only, not scenario assumptions, numerical methods or tolerances.


## 13 September: workbook XML intake hardening

Inspect every workbook ZIP member with a declaration-aware XML parser before downstream workbook reading. Reject DTDs/entities regardless of UTF-8/UTF-16 encoding or part filename. Malformed known XML parts fail with a stable intake error. Small valid-ZIP regression cases reproduce prior encoding/extension bypasses and verify their rejection. This does not execute macros, refresh external links or change economic formulas.


## 13 September: built-in teaching cases without file handling

First use should offer an optional official-example route without workbook selection or JSON import. This supersedes requiring separate workbook/scenario-file handling in the main tutorial, while preserving own-workbook intake and optional advanced exchange. The direct World Bank download is pinned to the recorded bytes, checked before use and cached locally; internet is needed for initial acquisition, not subsequent cached exercises. The template remains outside application archives and MIT licensing. No private workbook or scenario inputs are sent to its publisher.

The prepared investment set consists of No investment, Larger assumed benefit and Smaller assumed benefit, with matched 8% interest, 4-year grace and 9-year maturity. These complete paths include their coordinated fiscal assumptions and are tied to the exact official illustrative workbook. Each opens as an unsaved draft for review, save and calculation. The main tutorial compares against No investment; it neither estimates investment returns nor treats a reference-baseline/control gap as an investment effect. Simpler generic exercises remain available separately.

This direction is implemented in the alpha.2 source. This reconciled candidate requires fresh source checks and independent artifact review. Final rebuilt artifacts, actual public availability and release-specific installation acceptance remain separate. The calculation engine and numerical evidence limits are unchanged; independent fresh Excel verification and a complete offline/network audit are not established by these checks.

## 13 September: bounded packet rendering performance

Packet rendering reuses measured line wraps only within one export and reuses identical spreadsheet style objects. Printable ASCII prefix fitting uses measured binary search with the bundled fonts; Unicode/control text retains sequential fitting. The cache is bounded and discarded on completion or failure. All report layouts, font assets, PNG resolution, SVG outlines, tables, provenance and output inventory remain unchanged. Same-input packet equivalence and performance acceptance are separate from numerical verification; a new application identity requires fresh prepared teaching results.

## 14 September: reconcile the next desktop source candidate

The 0.1.0a2 source carries the application corrections used online into the desktop code: built-in example acquisition and teaching cases, clearer input summaries, stale-comparison feedback and bounded packet text layout. The hosted wrapper and deployment configuration are outside this source change. The public documentation deployment workflow and responsive site styles retain their existing bytes.

Preserve the three teaching-resource files exactly. All numerical definitions, projection years, financing assumptions and shared explanations retain their reviewed values. The label Larger assumed benefit supersedes Earlier assumed benefit; this corrects the label without changing the timing or size of any assumption.

At this source-reconciliation stage, desktop launcher corrections and Open Anyway guidance required separate bundle implementation and acceptance. The [release notes](release-notes-0.1.0a2.md) now describe the package changes and distinguish them from platform acceptance. Fresh source checks and exact package review cannot establish fresh Excel verification, hosted security acceptance or signing.

## 15 September: preserve teaching-resource bytes during checkout

The built-in JSON assumptions retain LF line endings in Git checkouts through a scoped `.gitattributes` rule. A Windows-style checkout with `core.autocrlf=true` previously converted these resources to CRLF; building and installing a wheel retained the converted bytes and the integrity check refused them. The source archive includes the attributes file so the rule also survives source distribution.

This mechanical correction preserves every reviewed resource byte and the existing expected fingerprints. It changes no numerical definition, year, financing assumption, shared explanation or integrity-check behavior. A scratch Git regression exercises CRLF conversion with an unprotected control file and checks the protected resources. A macOS simulation establishes the conversion mechanism; actual Windows CI and final desktop-package acceptance require separate evidence.

## 15 September: combine platform documentation for alpha.2

The release documentation combines Windows extraction and missing-runtime guidance with the unsigned Mac approval and stopping steps. Both platform packages must carry the same documentation commit as the release tag. This documentation-only integration changes no application source, teaching assumption, evaluator identity or numerical tolerance.

Bundled status prose records the evidence available at package assembly. Later platform receipts belong with the matching release and must identify the exact archive, source commit, environment, steps and observed result. Keep every unperformed check explicitly unverified; a later passing test does not alter the historical assembly status or establish coverage beyond that test. Source/history admission, package admission, actual desktop acceptance and fresh Excel verification remain separate.
