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

New deliberately shared explanations are optional per driver and financing path, saved with scenario revisions and included in comparison-v3 JSON and PDF annexes. Missing explanations for adjusted drivers remain explicit. Existing private journals remain private. Additive workspace schema 3 migration does not rewrite earlier numerical records or promote private text. New scenario-file import and annual-output expansion are separate pending work.

## Visible analyst workflow

The selected input has an editable 21-year path, nearby expandable help and a shared explanation field. Direction colors also use text/sign cues and remain distinct from unsaved-edit markers. Blank values are unfinished, not zero. A complete-grid view and changed-input summary support review. The five steps distinguish loaded, manually reviewed, saved, calculated, compared and download-prepared states; none implies fresh Excel verification.

A current calculation/comparison loads Standard LIC-DSF and Policy briefing previews together. Full-width charts are the default; both remain available in a side-by-side layout. Each view has explicitly labelled PDF/PNG downloads. Both images are accepted only for one unchanged comparison. Changing numerical inputs, source or selection clears both. The chart heading and the legend labels of the selected cases are edited in one **Chart text** panel beside the previews. Editing them retains the previews with their saved text and pauses comparison and downloads. **Apply to both views** or **Discard edits and keep saved text** refreshes both views automatically when the selected calculations are current and numerical inputs are unchanged; neither action recalculates the scenarios. A saved revision that changes only a case's name, legend label or shared explanations keeps its current calculation; only changed inputs or financing terms require a new calculation. Text takeaways, one per indicator and derived by the same rule as the policy headlines, accompany the previews. The numerical engine, its selected-year output coverage, tolerances and sharing boundaries are unchanged. See the updated tutorial for the complete workflow.

## Documentation clarification

The row identifiers, units, year mapping and output coverage are consolidated in the [input/output reference](workbooks-inputs-outputs.md). [The tutorial](tutorial.md) uses only the separately supplied official illustrative workbook. Scenario-file re-import, annual output expansion and hosted calculation remain pending. [Exchange and recovery](exchange-recovery.md) distinguishes current export records from a private workspace backup.

## 11 September: round 002 design slice (Claude Code implementation, independently reviewed)

Outward chart text is edited beside the previews: one **Chart text** panel in step 5 holds the heading and one legend label per selected case, with counters and a shared apply/discard pair. A legend change saves a new revision of the case; a revision that changes only the name, legend label or shared explanations keeps the calculation of the revision it was saved from (`store._numerical_base_revision`), while any change to inputs or financing terms, including a restore after an intervening change, still requires calculation. The exported `revision` is the current saved revision and `result_hash` still identifies the unchanged result.

State copy was made truthful: the step navigation no longer points backwards after a comparison, a draft edit that clears previews says so, a stale heading from another tab is reloaded automatically (or the draft is kept and the recovery button named), a single case compared with itself is flagged, and a chart render failure names the fix. Input safety: typographic minus signs pasted into number fields are converted or leave the field unfinished instead of flipping the sign; blank-year errors focus the visible year box; financing terms are checked before save; the scenario name is required; legend labels are checked for emptiness, duplicates, paths and the reserved “Reference baseline” at save time; intake refusals are plain sentences.

Presentation: colours mean the same in both chart views (baseline navy, emphasised case cyan, comparator gray); the standard overview has one legend and labelled threshold lines; the analyst's heading is the page title with the view name as a kicker; policy headlines name the comparator and the unit (“Lower growth is 1.1 pp of GDP above Growth control in 2044”) and the app lists the same sentences as text takeaways; negative numbers use a typographic minus; the sampled-points caveat is printed once per page; annex driver labels are bold. Download names are `scenario-comparison-standard`, `scenario-comparison-policy` and `scenario-comparison-data.json`. Indicator names on screen match the exports. The comparison table shows two decimals and no difference column for the comparator.

Deferred with reasons: connector length in the policy overview (a relative-difference encoding would change the chart's meaning; decision requested), one paper size for all PDF pages (layout risk for long headings; separate slice), keeping previews on screen while a draft is dirty (conflicts with the “changing inputs clears both” contract; decision requested), a revisions list and restore, and a glyph check at heading apply time.

### 11 September, corrections after Codex review (R2-CX-01 to R2-CX-04)

Legend labels and the heading are applied through one atomic store operation (`ScenarioStore.save_chart_text`, route `/api/chart-text`): all values validated first, all expected revisions checked in one `BEGIN IMMEDIATE` transaction, complete rollback on any refusal, and the final label set validated as a whole so swaps are accepted and duplicates refused. After any chart-text apply, discard or automatic conflict reload, the open case is reloaded as one coherent editor snapshot (inputs, financing terms, explanations, revision, result state) with an unsaved journal draft preserved; a new revision token is never combined with older editor inputs. The inline calculation status beside the Calculate button is derived from the actual state on every exit path (refused start, failed or interrupted job, review-required result, a newer draft during the run). No engine, evidence, tolerance or privacy behavior changed.
