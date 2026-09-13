# Read both chart views

Both views consume the same saved calculations. Changing view must not recalculate economics, replace the reference baseline, change the selected comparator or upgrade verification status. Select one to four saved scenarios from one workbook, with distinct outward-facing labels of no more than 40 characters.

## Standard LIC-DSF

Use this view for analysts familiar with IMF/World Bank output conventions. It retains familiar debt-indicator names, baseline/scenario distinctions, the external four-panel arrangement followed by the two supported public-debt panels, and threshold or benchmark lines labelled with their value on each panel. One legend serves all six panels of the overview; each detail page carries its own legend under the chart. Colours mean the same in both views: the reference baseline is muted gray, the comparator is gray, and alternatives in shared-label order use cyan, navy and purple. Line styles and markers also differ; colour does not indicate a policy judgment.

It is a supported subset, not a reproduction of the complete official stress figure. Historical and tailored stress scenarios and public debt service/revenue are omitted. Familiar styling does not imply institutional endorsement.

## Policy briefing

Use this view to inspect differences from the chosen comparison case over all reported years. The policy preview and individual PNG/SVG charts plot percentage-point differences, with a zero reference line. Positive means a higher ratio and negative means a lower ratio; neither is an automatic judgment about a plan. Standard LIC-DSF retains the corresponding levels and thresholds.

Every selected alternative receives a text summary for the chosen indicator: latest comparable observation, smallest and largest reported difference, whether the difference changes sign, and missing coverage. Both PDF reports include these summaries for all six indicators. These are descriptive facts, not estimates of benefits or causal claims. A reported range cannot establish an annual peak or a first threshold crossing.

The policy PDF also includes a compact snapshot at the last reported year. Dots show levels and connectors show distance from the comparator. Every row carries its value and difference. Missing final observations stay unavailable; they are not silently replaced with earlier values. Colours and marker shapes match the time-path charts, with alternatives ordered by shared label. No case is selected for emphasis because it was clicked first or had the largest result.

Each indicator uses its own difference or zoomed snapshot scale; compare numbers, not distances across indicators. A displayed `≈0.00` is a nonzero difference below 0.005 percentage points. Exact zero is `0.00`. Endpoint labels identify the actual final available observation, including its year when it differs from the last reported year. Arrowheads connect displaced labels to that observation. Full-precision values remain in the data files.

## What accompanies a chart

- The comparator and reference baseline remain explicit.
- Time-path axes retain workbook years and ratio units and include zero or observed negative values. Overview dot panels explicitly disclose their separate zoomed comparison scales.
- Threshold or benchmark values include their supported source cells. An unavailable threshold is stated as unavailable.
- Missing or error values remain gaps. Connecting lines are visual guides between samples.
- Evidence and coverage limitations remain visible.
- Exact matches to the recorded official example retain the Ghana-labelled, purely illustrative disclosure on every page. A country label or filename alone does not establish that provenance.

The app provides PNG and vector SVG for the selected individual indicator. PDF includes that overview and one larger page per indicator. Use the larger PDF pages when the overview is too small for projection or print. Download the data-and-assumptions JSON companion for full numerical precision and input context. Chart titles and displayed numbers are formatted for readability; the saved record is unchanged.

The app's table provides an alternative to reading values from a chart. The renderer also exposes a full-precision `comparison_summary` helper for accessible table integrations. Raster charts and the generated PDF are not themselves a complete accessible, tagged document. See [accessibility status](accessibility-platforms.md).

Current PDF exports add a variable-length shared-explanation annex after the seven chart pages, one section per selected scenario. Every annex page retains source identity, comparator, evidence and illustrative-data disclosure where applicable. Valid long explanations paginate; they are not truncated. Individual PNG/SVG exports contain charts only; the packet carries all figures with tables, reports and evidence.

## Review and download in the app

A current calculation/comparison shows both previews together, full width by default, with text takeaways above them. On screens at least 1,800 pixels wide, **Show charts side by side** is available; click a preview to open it at full size. Each chart has named PDF, PNG and SVG downloads. PDFs contain every indicator; PNG/SVG names include the selected metric. Keep the JSON companion (`scenario-comparison-data.json`) for assumptions and full precision. See [the worked tutorial](tutorial.md) for the complete download path and [chart text](chart-context.md) for outward text.

Input, source and selection changes clear the displayed comparison. Save and calculate changed scenario inputs before export. While chart text (heading or legend labels) is unapplied, existing previews retain the saved text and comparison/downloads are paused. Choose **Apply to both views** or **Discard edits and keep saved text** to refresh both previews automatically when selected calculations are current and numerical inputs are unchanged. Heading and legend changes do not change numerical results.

[Documentation index](README.md)
