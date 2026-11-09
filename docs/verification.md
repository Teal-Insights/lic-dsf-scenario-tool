# What has been checked, and how to check it yourself

A calculation can complete before it has been independently verified against Microsoft Excel. The app keeps these claims separate so you can judge the evidence attached to a result.

## Different checks answer different questions

| Check | What it tells you | What it does not establish |
| --- | --- | --- |
| Workbook fingerprint | Whether two people have the same exact file | Correct assumptions or calculations |
| Layout and input checks | Whether the file matches the supported structure and inputs are complete | Support for every version of the LIC-DSF template |
| Saved-workbook consistency | Whether selected recalculated values agree with values already saved in the workbook | A fresh Excel recalculation of your changed scenario |
| Application regression | Whether a new run reproduces our recorded example outputs | Independent confirmation that the evaluator implements every Excel feature correctly |
| Cross-platform comparison | Whether tested Mac and Windows runs agree within the fixed tolerance | Acceptance on every laptop or institutional configuration |
| Fresh Excel comparison | Whether the same inputs agree with a separately recalculated Excel workbook | Economic plausibility or official endorsement |

**This preview is not fully Excel-verified.** One scoped comparison is recorded below. A successful calculation remains labelled pending that check. The scenario assumptions still require an analyst's judgment even if a numerical comparison passes.

## Reproduce the official-example regression check

This technical check is optional. You can follow the [browser walkthrough](tutorial.md) without installing a development environment.

1. Obtain the source archive for the exact release you want to check. Follow the technical installation instructions in [source installation](source-installation.md). Use an isolated Python environment.
2. Download the unchanged workbook from the [official template source](template-source.md). Keep the Ghana-labelled data explicitly illustrative. Do not resave the workbook before this check.
3. From the extracted source directory, run:

```sh
python scripts/verify_official_example.py /path/to/LIC-DSF-IDA21-Template-08-12-2025-vf.xlsm --output ../verification-result.json
```

Replace the workbook path with your actual location. Put quotes around a path containing spaces. Choose a new output filename. The script refuses to overwrite an existing file or accept a different workbook fingerprint.

The script calculates a no-change control and a lower-growth case. It compares the complete recorded scenario/output fields with the checked-in reference in `tests/fixtures/official-example-regression.json`. It checks structure, missing values, spreadsheet error strings and finite numerical values. The absolute numerical tolerance is fixed at **0.000001**, with no relative tolerance and no option to loosen it.

On 5 November 2026 the no-change control matched this reference: 606 leaves within the fixed tolerance. The lower-growth case did not finish on that library revision, because it rejected a negative customized-scenario delta. On 6 November 2026, after the pin moved to `e0f5a8c2359e6931bb43adfdcb16a754232b2ffd`, both the no-change control and the lower-growth case matched the same reference: 606 leaves each. The reference was not rebaselined, and neither run was a fresh Excel recalculation. On 8 November 2026 the pin moved to `05d7f03862348df18d2b45a5d4a86152836edda4`. That official-example regression was not rerun on this revision. A mismatch or an incomplete case is not a reason to edit the fixture or the tolerance.

When a later revision does reproduce the reference, a successful run reports:

```text
PASS control: 606 checked values/fields
PASS lower-growth: 606 checked values/fields
PASS both application regression cases. Fresh Excel verification was not performed.
```

The local JSON receipt records the workbook identity, reference-file identity, calculation runtime and check outcomes. It does not include the original workbook or your file path. Keep the exact release with the receipt when reproducing the check later. A printed success line is not a substitute for retaining and inspecting that evidence.

The reference consists of application-generated results from the official illustrative workbook. It is a regression reference, not an independent Excel golden master. Tiny floating-point differences can occur between operating systems, so agreement within the stated tolerance is distinct from byte-for-byte or exact numerical equality.

## Run the source checks

With the package installed and Node.js 24 available, run:

```sh
python -m unittest discover -s tests -v
python scripts/check_javascript.py
python -m pip install ruff==0.16.7
python -m ruff check src tests scripts
```

The Python tests cover component behavior, including validation, saved-state and export contracts. On the pinned revision, the generated-library checks passed for a negative growth delta, a projection year carried by cached formula headers, and import of financing terms typed over Customized Scenario-External C21, C23 and C24. The JavaScript suites check interface handlers with neutral synthetic data. They do not launch a browser or calculate a real workbook. The initial lint gate targets implementation errors. Installation, actual browser interaction, package downloads and independent numerical checks remain separate evidence.

The [CI workflow](https://github.com/Teal-Insights/lic-dsf-scenario-tool/actions/workflows/checks.yml) runs these checks on Linux, Windows and Mac hosted runners. A workflow file is not proof that a run passed. Release notes must link the actual runs for the published candidate and distinguish source checks from downloadable desktop-package acceptance.

## Alpha.2 source-candidate checks

The 0.1.0a2 source adds reproducible checks for fixed-publisher example retrieval, corrupt-cache refusal, exact teaching-resource hashes and workbook/year binding. JavaScript checks exercise loading each prepared draft, preserving saved work, both desktop chart assignments and stale-download rejection. Summary checks retain tiny nonzero inputs, unfinished values and edits reset to zero. Text-wrapping checks compare the optimized renderer against its prior algorithm, including combining characters, and verify that the bounded packet cache is discarded after success or failure.

The label-only correction is reflected in the expected teaching label; all three input resources retain their pinned bytes. The numerical evaluator, reported-year definitions, intake hardening and locked comparison tolerance are unchanged. The release candidate needs fresh runs of the commands above and exact wheel/source-archive inspection. These checks do not establish desktop launcher acceptance, fresh Excel verification, hosted security acceptance or current CI success.

### Teaching-resource checkout integrity

The three built-in JSON resources are checked against fixed SHA-256 fingerprints before loading. Git must preserve their canonical LF bytes. `.gitattributes` limits that rule to these resources and is included in the source archive.

To run the focused installed-resource and Git checkout checks from the source root:

```sh
python -m unittest discover -s tests -p test_builtin_investment.py -v
python -m unittest discover -s tests -p test_resource_checkout.py -v
```

The checkout test uses a temporary Git repository with `core.autocrlf=true` and `core.eol=crlf`. An unprotected text file must become CRLF while all three resource hashes remain unchanged. The test requires Git and does not change your working checkout or global Git settings.

A local macOS before/after reproduction also builds and installs a wheel from each scratch checkout. Without the attributes rule, the installed resources have CRLF bytes and both normal-load tests fail the integrity check. With the rule, source, wheel and installed resources retain the pinned bytes. This is evidence for the checkout and packaging correction, not actual Windows acceptance. Required Windows CI and desktop launch checks are separate evidence. This local reproduction establishes neither; consult the [release evidence](release-notes-0.1.0a2.md#release-evidence) for results tied to the exact source commit and archive.

## Compare a scenario with Excel

A fresh Excel comparison requires the exact workbook and complete scenario definition, including financing treatment. Work on a copy and preserve the original. Enter the same customized-scenario inputs, recalculate in desktop Microsoft Excel, save the recalculated copy and compare the corresponding output cells with the app's full-precision results.

The [input/output reference](workbooks-inputs-outputs.md) identifies the supported rows, years and indicators. The exported comparison JSON includes the input definition and output cell references. Compare the same cells and units; do not compare rounded chart labels. Keep missing values and spreadsheet error classes distinct from numbers.

Retain the original and recalculated workbook fingerprints, Excel version/platform, input mapping, recalculation procedure, result differences and fixed tolerance. Record the first divergence and investigate it. This describes the evidence needed. The receipt below is one such comparison. This release has no automated Excel-verification procedure.

### 9 November 2026: official illustrative cases

Desktop Microsoft Excel recalculated a separate byte copy of the official illustrative workbook for **No investment** and for **Larger assumed benefit**. The publisher file kept its original bytes. Its SHA-256 is `3a0a0b80c7cbc95ac953f25ecae0b437129d669ceb8aeefb54ab86dc8727ea86` (5,504,930 bytes).

Excel was 16.0.20527.20112, 64-bit, on 64-bit Windows. Macros were disabled, workbook events did not run, and external links were not updated. Calculation stayed manual while the inputs were entered. `CalculateFullRebuild` then finished with calculation state done. Input 1 - Basics C18 stayed 2024.

Each copy received the cells the application writes: all 13 customized-scenario delta paths across the 21 projection years, and Customized Scenario-External C21, C23 and C24. Both cases enter interest 0.08, grace 4 and maturity 9, in place of the formulas that reference Input 7. No investment enters an explicit zero on every delta cell. Larger assumed benefit enters the built-in investment paths. The scenario definition hashes are `41bce725bd01d9d0e3a1ab6221918659222f365014c6a85ff1d049958dae6185` and `2631b5f012cb7b812ec340346dc891e652d4fb2d062ed32f7f726c93a2f3a7a6`.

On CPython 3.13.5, `lic-dsf-2025-08-12` 0.1.0 at `05d7f03862348df18d2b45a5d4a86152836edda4` with `generated_library_chart_series` calculated both cases as `computed_unverified`. Each matched the publisher's saved cache on 76 of 76 probes. The application still records `exact_excel: pending` for those runs. This receipt does not change that label.

Excel's calculated values were compared with the library samples for the same inputs. The check used absolute tolerance `1e-6`, exact error-class equality, and the 76 probes from the supported geometry: six indicators at offsets 0, 2, 5, 10, 15 and 20, for the reference-baseline row and the customized row, plus the four sentinels. There was no first divergence.

| Case | Probes within tolerance | Largest absolute difference |
| --- | --- | --- |
| No investment | 76 of 76 | 5.684341886080802e-14 |
| Larger assumed benefit | 76 of 76 | 5.684341886080802e-14 |

The four sentinels matched as text. The publisher cache of C21 is the formula result 0.07982399291786421. For No investment, the largest absolute difference between the library samples and that saved cache was also 5.684341886080802e-14. For Larger assumed benefit, 24 customized probes moved away from the publisher cache. The largest move was 7.946210060606688, on public PV of debt to revenue at the offset-5 customized cell. Those moved cells are inside the Excel pass above.

After both recalculations, CI Summary I11, I10, I13, I14 and L9 were 40, 180, 15, 18 and 55. The public-debt benchmark stayed 55. The library reads these cached threshold cells and does not recalculate them. The saved recalculated copies have SHA-256 `fc7fdec406494e87d577caf5fe76b14b4c6c36d55d6ce4f3bde9183b75dc9739` (No investment) and `c79049e05f4fbf30a477dd5664730ada9d11094d833e668c8566e4b073395142` (Larger assumed benefit).

The receipt covers this workbook, these two built-in definitions, this engine revision and these probes. Smaller assumed benefit, other outputs, other workbooks and other machines are outside it.

## If a check fails

Check the exact release, workbook identity, complete input paths and financing settings first. Retain the failed result privately. Do not change the reference values or tolerance just to get a pass. Send a non-confidential description through [feedback](feedback.md), or use the current private reporting guidance for a security concern. Do not attach a Ministry workbook or private logs to a public issue.
