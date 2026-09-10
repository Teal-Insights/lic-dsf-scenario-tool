# Choose a chart view

Both views consume the same saved calculations. Changing view must not recalculate economics, replace the reference baseline, change the selected comparator or upgrade verification status. Select one to four saved scenarios from one workbook, with distinct outward-facing labels of no more than 40 characters.

## Standard LIC-DSF

Use this view for analysts familiar with IMF/World Bank output conventions. It retains familiar debt-indicator names, baseline/scenario distinctions, the external four-panel arrangement followed by the two supported public-debt panels, and threshold or benchmark lines.

It is a supported subset, not a reproduction of the complete official stress figure. Historical and tailored stress scenarios and public debt service/revenue are omitted. Familiar styling does not imply institutional endorsement.

## Policy briefing

Use this view to discuss a selected comparison with policymakers. The overview compares named rows at a labelled sampled year for each indicator. Every row has its actual value and difference from the selected comparator in percentage points. Reference-baseline and scenario rows remain distinct. Dots show levels, and horizontal connectors show their distance from the comparator. The first selected case other than the comparator is emphasised.

Each indicator uses its own zoomed scale; compare the numeric differences, not lengths across panels. This warning is visible on the overview. Thresholds appear as sourced text so a distant threshold cannot compress a small scenario difference. Use Standard LIC-DSF or the detailed PDF pages for the full time path and threshold geometry. A displayed `≈0.00` means a nonzero difference smaller than 0.005 percentage points; the JSON companion retains its exact value.

The chosen year is the latest sampled observation with numeric values for the emphasised case and comparator. If none exists, the panel uses the latest numeric comparator observation, or the final saved year if the comparator is also missing. Missing/error rows are shown as unavailable, never zero. Detailed PDF pages retain time-path charts and supported sentence headlines; they do not select the largest apparent effect. Their endpoint labels state the actual value, and arrowheads connect displaced text to the data point.

A headline such as “Scenario A is 3.0 pp lower in 2044” means that this saved ratio is three percentage points below the selected comparator at that sampled year. Read the indicator and units immediately below it. It does not mean a causal effect, a three-percent change or an annual peak. If that year is missing, any reported comparison uses a labelled earlier observed year. Review-required results receive a neutral review message.

## What accompanies a chart

- The comparator and reference baseline remain explicit.
- Time-path axes retain workbook years and ratio units and include zero or observed negative values. Overview dot panels explicitly disclose their separate zoomed comparison scales.
- Threshold or benchmark values include their supported source cells. An unavailable threshold is stated as unavailable.
- Missing or error values remain gaps. Connecting lines are visual guides between samples.
- Evidence and coverage limitations remain visible.
- Exact matches to the recorded official example retain the Ghana-labelled, purely illustrative disclosure on every page. A country label or filename alone does not establish that provenance.

PNG provides the complete six-panel overview. PDF includes that overview and one larger page per indicator. Use the larger PDF pages when the overview is too small for projection or print. Download the data-and-assumptions JSON companion for full numerical precision and input context. Chart titles and displayed numbers are formatted for readability; the saved record is unchanged.

The app's table provides an alternative to reading values from a chart. The renderer also exposes a full-precision `comparison_summary` helper for accessible table integrations. Raster charts and the generated PDF are not themselves a complete accessible, tagged document. See [accessibility status](accessibility-platforms.md).
