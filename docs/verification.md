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

**Fresh Excel verification remains pending.** Do not describe this preview as fully Excel-verified. The scenario assumptions still require an analyst's judgment even if a numerical comparison passes.

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

A successful run is expected to report:

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

The Python tests cover component behavior, including validation, saved-state and export contracts. The JavaScript suites check interface handlers with neutral synthetic data. They do not launch a browser or calculate a real workbook. The initial lint gate targets implementation errors. Installation, actual browser interaction, package downloads and independent numerical checks remain separate evidence.

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

A local macOS before/after reproduction also builds and installs a wheel from each scratch checkout. Without the attributes rule, the installed resources have CRLF bytes and both normal-load tests fail the integrity check. With the rule, source, wheel and installed resources retain the pinned bytes. This is evidence for the checkout and packaging correction, not actual Windows acceptance. Fresh required Windows CI on the repaired candidate and desktop launch checks remain pending.

## Compare a scenario with Excel

A fresh Excel comparison requires the exact workbook and complete scenario definition, including financing treatment. Work on a copy and preserve the original. Enter the same customized-scenario inputs, recalculate in desktop Microsoft Excel, save the recalculated copy and compare the corresponding output cells with the app's full-precision results.

The [input/output reference](workbooks-inputs-outputs.md) identifies the supported rows, years and indicators. The exported comparison JSON includes the input definition and output cell references. Compare the same cells and units; do not compare rounded chart labels. Keep missing values and spreadsheet error classes distinct from numbers.

Retain the original and recalculated workbook fingerprints, Excel version/platform, input mapping, recalculation procedure, result differences and fixed tolerance. Record the first divergence and investigate it. This describes the evidence needed; it is not a completed or fully automated Excel-verification procedure for this release.

## If a check fails

Check the exact release, workbook identity, complete input paths and financing settings first. Retain the failed result privately. Do not change the reference values or tolerance just to get a pass. Send a non-confidential description through [feedback](feedback.md), or use the current private reporting guidance for a security concern. Do not attach a Ministry workbook or private logs to a public issue.
