# Try an illustrative investment, from assumptions to briefing

**Source candidate: `0.1.0a2`.** This guide describes the next built-in walkthrough. Alpha.2 desktop packages and their installation checks are pending. The published alpha.1 predates this route. See the [release notes draft](release-notes-0.1.0a2.md) for scope and remaining checks.

Learn the tool without choosing a workbook file or importing a scenario file. The app obtains the official illustrative workbook and provides three prepared teaching cases. You review the assumptions, save and calculate each case, compare the results and download a briefing.

**These are illustrative assumptions, not real investment modeling or estimated returns.** The app calculates what follows from the assumptions; it does not estimate whether an investment will deliver them. The workbook's Ghana-labelled sample data are not an official Ghana forecast or DSA. Investment is one use of this general scenario analysis tool.

[Install first](installation.md) · [Methods and limits](methodology.md) · [Optional growth exercise](growth-tutorial.md)

## 1. Start the official example

In step 1, select **Download and try the official example**. This downloads the unchanged template directly from the World Bank, checks its file fingerprint and stores it locally. Allow internet access for this first download. No private workbook or scenario inputs are sent in that request. The World Bank's download service receives the usual connection information, such as your IP address.

When the verified example is already available, select **Try the official illustrative example**. You can use the cached workbook and the prepared cases offline. The template is obtained separately from the publisher; it is not included in the application download or covered by the app's MIT license. [Template source](template-source.md) records its origin and exact identity.

If the download fails, check your connection and retry. A changed or damaged file is refused rather than silently substituted. A manual workbook chooser remains available for your own supported workbook, but it is not needed for this exercise.

## 2. Review the baseline

The official example uses projection years **2024–2044**. The baseline table shows selected observations: **2024, 2026, 2029, 2034, 2039 and 2044**. Check the source and years, then select **I have checked the projection years and baseline values** and **Continue to create a scenario**.

This records your review. It does not independently verify the workbook in Excel. The five workflow steps show progress, not certification.

## 3. Load, review and calculate the comparison case

In the blue **Try an illustrative investment** panel, under **Prepared teaching case**, choose **1. No investment · comparison case**. Select **Load illustrative case**. It opens an unsaved draft with the chart label **No investment**.

Review its zero macro adjustments and its financing terms: **8% interest, 4-year grace and 9-year maturity**. These terms are held constant across all three prepared cases. This case is a customized no-new-investment control; it may differ from the workbook's reference baseline.

Select **Save scenario**, then **Calculate and show results**. Wait for completion before moving on. Loading supplies inputs; saving preserves them; calculation produces results. None of these steps claims fresh Excel verification.

## 4. Try the two complete investment cases

Repeat the same steps for **2. Investment · larger assumed benefit** and **3. Investment · smaller assumed benefit**: select the case, **Load illustrative case**, review, **Save scenario**, then **Calculate and show results**. Their chart labels are **Larger assumed benefit** and **Smaller assumed benefit**. Save or discard outstanding draft edits before loading another case.

| Assumption | Larger assumed benefit | Smaller assumed benefit |
| --- | --- | --- |
| Upfront investment, 2027–2029 | 0.5% of each year's baseline GDP | Same |
| Maintenance, 2030–2044 | 0.05% of each year's baseline GDP | Same |
| Assumed extra real GDP growth, 2030–2034 | +0.2 percentage points each year | +0.1 percentage points each year |
| Imported inputs, 2027–2029 | 0.2% of each year's baseline GDP, included in the investment cost | Same |
| Financing | 8% interest, 4-year grace, 9-year maturity | Same |

These are assumptions chosen for teaching. The example makes no promise of large investment returns and does not compare alternative financing offers. Read each changed input's shared explanation beside the editor; these explanations travel with the briefing.

**Why are some annual entries more complicated than this table?** The template accepts ratio adjustments. The prepared cases translate the investment story into coordinated spending, revenue and grant paths as GDP changes. Existing non-investment primary spending and grants keep their baseline nominal levels, while revenue excluding grants keeps its baseline GDP share. The growth assumption raises the GDP level even after the extra growth ends. Smaller spending or grant ratios therefore do not automatically mean nominal spending cuts or new grant funding.

Use **Review or edit every year and input** to inspect the complete paths. Changing only growth while leaving those linked paths unchanged no longer preserves that fiscal interpretation. For your first comparison, use each complete prepared case. For independent editing practice, use the simpler [growth sensitivity](growth-tutorial.md).

## 5. Compare with No investment

Under **4. Compare saved scenarios**, select the three calculated cases. Set **Measure changes against** to **No investment**, then select **Compare selected scenarios**. Open **Inspect the numerical comparison table**.

The differences are each scenario minus **No investment**, in percentage points of the indicator. The reference baseline remains visible separately. Do not treat its difference from the customized control as an investment effect.

Inspect both **Standard LIC-DSF** and **Policy briefing** views. Standard shows levels and thresholds; Policy briefing makes differences from the comparison case easier to see. Choose an indicator to update both views. Look across indicators and reported years before drawing a conclusion. Lines between the six observations do not identify annual peaks or exact threshold-crossing dates.

The useful question is: under these stated assumptions, how do upfront costs and assumed macroeconomic benefits change the debt indicators? Different assumed benefits can produce different tradeoffs. The tool does not tell you which benefits will actually materialize.

## 6. Make a briefing you can share

In **Chart text** beside the previews, use **Illustrative investment: benefits and financing costs** as the heading. Select **Apply to both views** and inspect both charts. You can edit the legend labels here too. Text changes do not change numerical assumptions; unsaved text pauses downloads until you apply or discard it.

Select **Download briefing packet (.zip)**. Open its **READ ME**, then the Standard LIC-DSF and Policy briefing PDF reports. The 35-file packet includes both reports, six PNG and six SVG charts in each style, an Excel workbook, five CSV tables, full-precision comparison data and a file manifest.

Check the comparator, units, projection years, assumptions, shared explanations and illustrative disclosure. The workbook's **Read me first** sheet explains its tables. The packet excludes your original workbook and private journal. Review actual files before sharing; shared text and assumptions can still contain confidential information in your own analyses.

A file fingerprint identifies the exact source or output, rather like an automatically generated reference number. It helps a colleague check that they are using the same file; it does not prove that the economic assumptions are right. [Reading a briefing](reading-briefing.md) explains the evidence in plain language.

## 7. Return to your saved work

Save any private journal edits separately. Wait for jobs to finish, stop the app with **Control-C** in its command or Terminal window, then reopen the same launcher. In step 1, reopen the saved workbook to retrieve the three cases. Unsaved drafts are not retained. A changed calculation runtime may require recalculation.

The built-in examples require no JSON downloads or imports. The optional **Share or reuse a scenario file** controls are for exchanging your own prepared assumptions with a colleague or reusing them in another workspace. They are an advanced route, distinct from the briefing packet. See [exchange and recovery](exchange-recovery.md) when you need them.
