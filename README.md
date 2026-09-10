# LIC-DSF Scenario Analysis Tool

Explore customized scenarios from a supported LIC-DSF IDA21 workbook in a local browser workspace. Keep your original workbook, save alternative assumptions and private reasoning, compare current calculations, and export charts with numerical data.

**Work in progress.** This source preview implements a limited input and output set. Fresh installation, an independent analyst tutorial, Windows operation and exact live-Excel comparison are not yet accepted. It is not an official IMF/World Bank product or a Digital Public Goods recognised solution.

## Start here

1. Follow [installation](docs/installation.md) to run the local application.
2. Use [the tutorial](docs/tutorial.md) to upload, save, calculate, compare and export.
3. Read [methods and evidence](docs/methodology.md) before interpreting a result.
4. Review [privacy and recovery](docs/privacy-recovery.md) before using sensitive data.

You supply the workbook. The application does not require Excel to calculate: it uses a pinned Python spreadsheet evaluator. This is a distinct calculation environment whose agreement with Excel must be tested, not assumed. The application does not run macros, refresh external links or modify the original workbook.

The optional [World Bank IDA21 example](https://thedocs.worldbank.org/en/doc/f0ade6bcf85b6f98dbeb2c39a2b7770c-0360012025/new-lic-dsf-template) contains Ghana-labelled **purely illustrative** worked-example data. Those values are not an official Ghana forecast or DSA. The template binary is obtained separately from its publisher; this repository does not redistribute it.

## What the preview supports

- Thirteen customized-input paths over 21 workbook years, plus three external financing terms.
- Separate reference-baseline, as-supplied customized and selected-scenario values.
- Saved scenario revisions and a private reasoning journal.
- Comparisons from the same workbook, with an explicit selected comparator.
- Standard LIC-DSF and Policy briefing charts using the same saved results.
- PDF, PNG and JSON data-and-assumptions exports.
- Optional [per-workbook shared chart labels](docs/chart-context.md), with visible source identifiers.

Results cover six debt ratios at six sampled years. They do not reproduce the complete stress-test suite, all annual outputs or official risk ratings. Pending verification remains visible. See [chart guidance](docs/charts.md), [accessibility and platform status](docs/accessibility-platforms.md) and [DPG evidence and gaps](docs/dpg-evidence.md).

Developer references: [architecture](docs/architecture.md), [JSON contracts](docs/data-contract.md), [contributing](CONTRIBUTING.md), [security](SECURITY.md) and [third-party notices](THIRD_PARTY.md).

## Ownership and contributions

Copyright 2026 Teal Insights. Application code is MIT licensed; consult the distribution's LICENSE. Workbook, dependency and font rights are separate. No institutional endorsement is implied.

For a defect report, provide the application version, operating system, steps and a reviewed, non-sensitive description of the error. Do not attach a workbook, database, journal, screenshot or log containing analytical or personal data to a public issue. A private security-reporting route and formal contribution/release policies remain release requirements.
