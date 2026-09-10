# First comparison: a small growth adjustment

This walkthrough follows the preview's visible controls. It is awaiting an independent analyst walkthrough; it does not predict a debt-ratio change or claim Excel verification. Use the public illustrative example for learning, or a supported workbook you are authorised to process.

## 1. Obtain and check the workbook

Download `LIC-DSF-IDA21-Template-08-12-2025-vf.xlsm` from the [World Bank template page](https://thedocs.worldbank.org/en/doc/f0ade6bcf85b6f98dbeb2c39a2b7770c-0360012025/new-lic-dsf-template) or its [recorded direct download](https://thedocs.worldbank.org/en/doc/f0ade6bcf85b6f98dbeb2c39a2b7770c-0360012025/original/LIC-DSF-IDA21-Template-08-12-2025-vf.xlsm).

Its Ghana-labelled values are **purely illustrative**, not an official Ghana forecast or DSA. Keep this disclosure with every example-derived export. The original download recorded on 9 September 2026 has SHA-256 `3a0a0b80c7cbc95ac953f25ecae0b437129d669ceb8aeefb54ab86dc8727ea86`. A different hash identifies a different file; it does not by itself mean an uploaded workbook is unsupported. No template binary is distributed with this software.

In **1. Choose your workbook**, select the file and choose **Upload and check**. If configured, **Try the official illustrative example** loads the same separately supplied example. In section 2, check the workbook identity, supported structure and input years. The initial baseline table shows saved workbook values, not freshly recalculated Excel results. Resolve unsupported-structure findings before continuing.

## 2. Save a comparator

Choose **New scenario with zero adjustments**. Use internal name `Zero adjustments` and shared label `Illustrative zero adjustments`. Review the complete grid: all 273 adjustments should be explicit zero. Leave the external financing override unchecked to preserve supplied values and formulas.

Choose **Save scenario**, then **Calculate saved scenario**. Wait for completion and read the evidence. Zero adjustments mean no additions to the customized inputs; they do not turn the customized output into the workbook's reference Baseline. To inspect the workbook's existing customized inputs instead, use **Import workbook’s customized scenario** as a separate case.

## 3. Duplicate and change one input

Open the saved zero-adjustment case and choose **Duplicate this scenario**. Give the draft internal name `Growth adjustment` and shared label `Illustrative growth adjustment`.

Under **Apply a change over a period**, choose **Real GDP growth**. Select the first input year in both year selectors and enter `-0.1`. Choose **Apply to draft**. This adds minus 0.1 percentage points to growth in that year; it is neither a growth level nor a 10% fall. Review the expanded year-by-year grid and confirm all other adjustments remain zero. Leave financing terms inherited.

Choose **Save scenario**, then **Calculate saved scenario**. A result is a calculation under the entered assumptions, not evidence that the assumptions will occur. If calculation or review findings prevent comparison, retain the saved case and investigate; do not treat failure as a zero effect.

## 4. Record reasoning and compare

With the saved revision open, expand **Private reasoning journal**, explain the illustrative assumption and choose **Save journal entry**. Entries are retained with revision numbers and excluded from shared exports. Saving a scenario does not automatically save an unfinished journal entry.

Select both calculated cases in section 4. Choose `Illustrative zero adjustments` as **Comparator**, then choose **Compare selected scenarios**. The table retains the reference baseline and reports differences against your selected case. A difference of 1 in a percentage ratio is one percentage point. Do not interpret sampled observations as a full annual series.

## 5. Review and export both views

Optionally enter a **Label for shared charts** and choose **Save label**. This outward text is saved for the selected workbook; it is separate from scenario names and private reasoning. Leave it blank for only the workbook identifier.

Choose **Standard LIC-DSF**, then **Preview charts**. Check shared labels, years, units, comparator, evidence and scope. Choose **Download PDF** and **Download PNG**. Repeat with **Policy briefing**. Switching view must not change the saved assumptions, selected cases, comparator or numeric table.

Choose **Download data and assumptions** for the JSON companion. Review it as well as the charts: it contains economic assumptions and results even though the private journal and internal names are excluded. Keep the illustrative-data disclosure with the files. Chart-only files do not contain the private reasoning journal or a complete assumptions table.

## 6. Confirm recovery and stale-result handling

Save all drafts, stop the app and restart with the same data directory. Reopen the workbook and saved cases. Confirm the saved revisions and journal entries remain. If the engine changed, calculate again before export.

To check a revision, change one input and save it. The previous calculation must not become the result for the new inputs. Recalculate that saved revision before comparing or exporting. An empty input is unfinished; restore an explicit number such as zero rather than expecting a blank to mean zero. Retain the original learning cases by duplicating before further experiments.

## Optional illustrative starting points

In section 3, expand **Optional illustrative starting points**. Choose lower GDP growth (−1 percentage point), higher primary expenditure (+1 point of GDP), or lower exports (−1 point of GDP), then choose **Create unsaved draft**. Each example changes only the first three projection years displayed for the loaded workbook, resets all other macro adjustments to zero, and inherits the workbook’s financing terms. These are learning examples, not recommendations or standardized IMF stress tests.

Review the named draft and actual years, edit as needed, then save and calculate. Creating the draft does not calculate, save, or change existing cases. Save or discard unfinished scenario and journal edits before choosing another starting point. Use a comparator with matching financing terms when interpreting a macro-only difference.
