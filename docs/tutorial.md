# Make a two-case illustrative briefing

Use the official public example to compare a no-change customized control with growth one percentage point lower for the first three projection years. You will save two cases, calculate them, inspect both chart views, download five files and reopen the saved work.

This is a sensitivity exercise. The Ghana-labelled sample values are purely illustrative and are not an official country forecast, DSA or policy recommendation. A zero-adjustment customized control can differ from the workbook's reference baseline.

[Documentation index](README.md) · [Install first](installation.md) · [Input reference](workbooks-inputs-outputs.md)

## 1. Load the unchanged public example

Download the file linked in [Template source](template-source.md). Keep it unchanged for this exercise. Opening and saving it in a spreadsheet application changes its identity and may change saved values.

In **1. Choose your workbook**, choose `LIC-DSF-IDA21-Template-08-12-2025-vf.xlsm` and select **Upload and check**. If your launcher provides **Try the official illustrative example**, you can use that button instead.

The app should accept the workbook and display the baseline table. Under **File fingerprint (SHA-256)**, confirm the fingerprint against the [recorded official SHA-256](template-source.md). The five workflow steps report progress, not a certification of the assumptions or Excel agreement.

## 2. Check the projection years and baseline

For the exact recorded example, the input horizon is **2024–2044**. The baseline table reports **2024, 2026, 2029, 2034, 2039 and 2044**. These are selected observations from the workbook's saved baseline values.

Check that the source, years and values are the ones you intended to load. Select **I have checked the projection years and baseline values**, then **Continue to create a scenario**. This checkbox records your review for the visit; it does not run a numerical check.

## 3. Save and calculate the control

In **Try an illustrative scenario**, choose **Growth: no-change control**, then **Create unsaved draft**. This starts a new draft with all 13 adjustment paths zero and financing inherited from the workbook.

Use `Tutorial control` as the **Scenario name in your workspace** and `Growth control` as the **Legend label on charts and exports**. The first name is internal; the second appears on both chart views, in the comparison table and in exported files. A counter shows the 40-character limit. The illustrative case prefills a shared explanation marked as an exercise; edit or keep it.

Select **Real GDP growth** under **Input to change**. Confirm all 21 entries are zero. Leave **Set new financing terms for this scenario** unchecked. You can inspect the full grid under **Review or edit every year and input**.

Select **Save scenario** and wait for it to succeed. If you want to retain private notes, enter them in the separate journal now and select **Save journal entry**. Then select **Calculate and show results**. Wait for the calculation to complete before continuing. Saving alone does not produce current results. A successful run can still state that fresh Excel verification is pending.

## 4. Save and calculate lower growth

Choose **Growth: −1 percentage point**, then **Create unsaved draft**. Name it `Tutorial lower growth` internally and `Lower growth` for sharing.

Select **Real GDP growth** and verify the complete path:

| Projection years | Growth adjustment |
| --- | --- |
| 2024–2026 | −1 percentage point each year |
| 2027–2044 | 0 each year |
| Every other customized input | 0 in all 21 years |
| External financing | Inherit supplied terms and formulas |

For example, a workbook growth assumption of 5% plus an adjustment of −1 percentage point gives 4%. The entry is a change, not a new growth level. This example does not describe the workbook's actual growth assumption.

In **Explain Real GDP growth (shared)**, replace the prefilled exercise text with: “Illustrative sensitivity: growth is one percentage point lower in 2024–2026, with no further growth adjustment afterward. All other customized inputs are zero and financing is inherited.” It will appear in PDF/data exports.

Select **Save scenario** and wait for it to succeed. If you want to retain private notes, enter them in the separate journal now and select **Save journal entry**. Then select **Calculate and show results**. A new draft, or a saved revision that changes inputs or financing terms, needs its own calculation; a revision that changes only the name, legend label or explanations keeps the current calculation. If you edit during a calculation, the newer draft remains unsaved and cannot use the earlier result as its current calculation.

## 5. Compare against the control

Under **4. Compare saved scenarios**, select the two calculated cases. Set **Measure changes against** to `Growth control`, then select **Compare selected scenarios**. Expand **Inspect the numerical comparison table**.

Check that both cases use the same workbook and reporting years. Differences are scenario minus selected comparator, measured in percentage points of the indicator. The reference baseline stays visible as its own channel. The comparator has no difference column in the numerical table: its difference from itself is zero. It need not equal the reference baseline.

For the exact recorded public example and this exercise, the 2044 policy overview displays these values (rounded):

| Indicator | Growth control | Lower growth | Difference |
| --- | --- | --- | --- |
| PV of PPG external debt / GDP | 27.58% | 28.67% | +1.09 percentage points |
| PV of total public debt / GDP | 36.33% | 37.79% | +1.46 percentage points |

The reference-baseline public-debt value is 37.22%, which illustrates why it must remain distinct from the 36.33% customized control. These are descriptive outputs conditional on the stated inputs, checked against saved-workbook probes. They are not freshly verified Excel results. If your values differ, check the exact workbook, all paths, financing choice and comparator before interpreting the difference. Do not adjust tolerances to force a match.

Do not assume all debt indicators move in the same direction or by the same amount. Read the actual table. The six sampled years cannot identify the annual peak or the first threshold crossing between them.

## 6. Review and download the briefing

Standard LIC-DSF and Policy briefing previews appear together. Use the standard panels to inspect debt paths and thresholds, and the policy view to explain differences at its stated year. Each policy panel has its own scale. A line between sampled years is a visual guide.

In the **Chart text** panel beside the previews, optionally enter `Illustrative growth sensitivity` as the **Heading on both chart views**. The same panel lists a **Legend label** field for each selected case, so you can rename `Lower growth` where the charts are. While you edit, existing previews retain the saved text and downloads are paused. Select **Apply to both views** to save your text, or **Discard edits and keep saved text** to reload the latest saved text. Both actions refresh the previews automatically when the selected calculations are current and numerical inputs are unchanged. Neither a heading nor a legend change requires a new numerical calculation; a legend change saves a new revision of that case with its calculation kept. Legend labels and the heading are outward text; review them deliberately. If another tab changed the heading and you have no unapplied chart-text draft, the app reloads the latest saved text, refreshes both views and asks you to download again. If you have unapplied text, it preserves that draft and asks you to choose **Discard edits and keep saved text**. Copy text you want to retain before discarding it.

Download and inspect all five files:

- **Download standard PDF** and **Download standard PNG**.
- **Download policy PDF** and **Download policy PNG**.
- **Download data and assumptions**, the JSON companion containing exact inputs, years, values and deliberately shared explanations.

The suggested chart filenames distinguish the views: `scenario-comparison-standard.pdf` and `scenario-comparison-policy.pdf`, with matching `.png` names. The JSON companion is `scenario-comparison-data.json`; it contains the shared comparison data for both views. If your browser adds a number to avoid a duplicate, open the file and check its content before renaming it.

The PDFs contain seven chart pages plus a variable-length shared-explanation annex. PNGs contain the six-panel overview only. Confirm that labels, comparator, source reference, units, selected years and pending evidence are present. The illustrative disclosure must remain attached. A download-prepared indicator does not prove a file reached your download folder; open the actual files.

Comparison JSON cannot be imported back into this app. Keep the original workbook and a private workspace backup if you need to continue the analysis later. [Exchange and recovery](exchange-recovery.md) explains the difference.

## 7. Stop and reopen

Save any private journal draft separately. Wait for calculations to finish, then stop the terminal application with Ctrl+C. Restart it with the same data directory and reopen the workbook from **Or reopen a workbook in this workspace**.

Confirm both cases and their shared explanations are present. Select and compare them again. Results may need recalculation if you changed the installed runtime. Use the [stopped-workspace backup procedure](exchange-recovery.md#back-up-and-restore-a-workspace) before upgrading.

## Use the editor on your own case

Select an input, enter **From year**, **Through year** and **Change to apply**, then **Apply to these years**. The range is inclusive and entries outside it remain unchanged. Type into individual year boxes when the path is irregular. Blank is unfinished; explicit zero adds no adjustment. A gold underline marks edits since the saved revision or initial draft, while signs and colors show positive, negative or zero values.

Use the changed-input filter to review affected rows and the explanation field to record the source or judgment behind each path. Check transfer/FDI signs and asset units in the [input reference](workbooks-inputs-outputs.md). Financing rates are replacement levels in percent; grace and maturity are whole years. Save after any edit. Changed numerical inputs or financing terms require calculation. A save that changes only the case name, legend label or shared explanation keeps an already-current calculation. Save the text, compare again and review the refreshed exports; unsaved text cannot be exported. If the result is already stale or absent, a text-only save does not make it current.
