# Accessibility and platform status

This is an experimental preview. The statuses below record evidence available at package assembly. Bounded Mac and Windows Server evidence exists for earlier builds; final alpha packages need their own checks. For later results, consult the [release evidence](release-notes-0.1.0a2.md#release-evidence) and match the tested archive fingerprint. An omitted result remains unverified. No WCAG conformance, complete assistive-technology acceptance or universal cross-platform support is claimed.

## Accessibility features and remaining work

The browser page has labelled controls, numbered navigation links, a visible keyboard-focus style, expandable help and a live status region. The input grid labels each field by economic input and workbook year. Comparison values appear in a table. Charts distinguish series using line styles and markers as well as colour, and retain units and years.

Those implementation choices need independent testing. Keyboard-only completion, screen-reader reading order and table associations, focus after validation errors, zoom/reflow, colour contrast, long labels and projected readability remain acceptance checks for the assembled release. Wide input tables require horizontal scrolling. The image alternative points to the numerical table; it does not narrate every series.

PNG is a raster image. PDF contains vector text and plots but is not certified as a tagged accessible PDF. JSON preserves full-precision data and assumptions but is not a substitute for usable nontechnical access. A release should provide an accessible table alongside charts and test it with its intended users.

## Platform evidence

| Area | Status recorded at package assembly |
| --- | --- |
| Python requirement | Source declares Python 3.11 or later; dependency/platform compatibility still needs verification |
| Excel installation | Not required by the Python calculation route; exact Excel verification is a separate pending activity |
| Browser | Local HTML interface implemented; no complete accepted browser matrix |
| macOS | Earlier installed browser/calculation/packet checks passed on Apple Silicon. Separate relocation and worker checks exist for earlier macOS14+ arm64 bundles; final downloaded Finder launch and a complete final-package walkthrough were unverified at assembly |
| Windows | Earlier package tested on Windows Server2022x64 as Administrator, without Excel: launch, upload, two calculations, charts, packet, scenario re-import and restart. Final-package execution and managed Windows11 ordinary-user acceptance were unverified at assembly |
| Linux | No accepted end-to-end platform test |
| Offline runtime | No hosted service or remote runtime assets intended; measured offline/network-behaviour acceptance remains pending |
| Installation | Earlier clean source installation tested; desktop package paths now documented. Each final download still requires exact acceptance |
| Recovery | Durable records and recovery instructions exist; independent full-workspace restore acceptance remains pending |

Record the exact application/dependency versions, OS, browser, test steps and observed result when closing a gap. Do not infer platform acceptance from a simulated test, packaged files or source branches alone.

## Visible analyst workflow

The selected input has an editable 21-year path, nearby expandable help and a shared explanation field. Direction colors also use text/sign cues and remain distinct from unsaved-edit markers. Blank values are unfinished, not zero. A complete-grid view and changed-input summary support review. The five steps distinguish loaded, manually reviewed, saved, calculated, compared and download-prepared states; none implies fresh Excel verification.

A current calculation/comparison loads Standard LIC-DSF and Policy briefing previews together. Full-width charts are the default; side-by-side layout is available only on wide screens. Each view has explicitly labelled PDF/PNG downloads. Both images are accepted only for one unchanged comparison. Changing numerical inputs, source or selection clears both. The chart heading and the legend labels of the selected cases are edited in one **Chart text** panel beside the previews. Editing them retains the previews with their saved text and pauses comparison and downloads. **Apply to both views** or **Discard edits and keep saved text** refreshes both views automatically when the selected calculations are current and numerical inputs are unchanged; neither action recalculates the scenarios. A saved revision that changes only a case's name, legend label or shared explanations keeps its current calculation; only changed inputs or financing terms require a new calculation. Summaries of every selected alternative accompany the chosen indicator; full reported-year summaries also appear in both PDFs. The numerical engine, its selected-year output coverage, tolerances and sharing boundaries are unchanged. See the updated tutorial for the complete workflow.


Individual SVG previews remain images with accessible descriptions, backed by text takeaways and the numerical HTML table. Vector rendering improves zoom clarity but is not itself screen-reader accessibility. The local Inter and IBM Plex Serif files eliminate reliance on installed fonts or an external font service. Keyboard, focus and narrow-screen behavior require actual browser checks for each delivery.
