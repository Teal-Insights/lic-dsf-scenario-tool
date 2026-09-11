# LIC-DSF Scenario Analysis Tool

Explore how alternative macroeconomic and financing assumptions change debt indicators in a supported World Bank LIC-DSF workbook. Save cases and their reasoning, compare them with a chosen control, and prepare charts with the underlying data.

**Work in progress.** This local application supports 13 customized input paths and six debt indicators at selected years. Fresh Microsoft Excel verification and actual Windows acceptance remain pending. It is not an official IMF/World Bank product or a formally recognized Digital Public Good.

## Get your first result

1. [Install and start a local workspace](docs/installation.md). A technical colleague may need to help with Python and dependencies.
2. [Run the public illustrative exercise](docs/tutorial.md). Save a no-change control and a lower-growth case, calculate both, and download a briefing.
3. [Use your own supported workbook](docs/workbooks-inputs-outputs.md). Check its projection years, units and baseline before changing assumptions.

The app runs in your browser on your computer. It preserves the original workbook and saves scenarios separately. Excel is not needed to run calculations: a pinned Python evaluator reads workbook formulas. Macros do not run and external links do not refresh. [Methods and evidence](docs/methodology.md) explain what its checks establish.

The separately downloaded [World Bank template](docs/template-source.md) contains Ghana-labelled **purely illustrative** worked-example data. It is not an official Ghana forecast or DSA. The repository does not include the workbook binary, and the software license does not grant rights to that asset.

## Work through five steps

| Step | What you do |
| --- | --- |
| Upload | Choose a completed supported workbook, or try the configured official example. |
| Check baseline | Review the projection years and saved baseline values. |
| Create scenarios | Edit annual assumptions, explain them, save a revision and calculate it. |
| Compare | Select calculated cases and choose which case differences are measured against. |
| Export briefing | Review both chart views, edit the heading and legend labels beside them, and download PDF, PNG and data-and-assumptions JSON. |

Each of the 13 inputs has a 21-year editor, period entry, unit/sign help and an optional shared explanation. Blank is unfinished; zero adds no adjustment. Financing overrides use a rate in percent and grace/maturity in years. A separate private journal retains notes excluded from briefing exports.

Standard LIC-DSF and Policy briefing charts appear together and use the same calculation. The reference baseline, workbook-supplied customized case and your saved scenario remain distinct. Current outputs contain six sampled years, so charts cannot establish annual peaks or first threshold crossings. [Read both chart views](docs/charts.md).

Growth, funding-cost and investment examples supply editable assumptions and matched controls. They do not estimate a policy effect or an investment return. Scenario-file download/re-import, complete annual outputs and online calculation are still pending. Comparison JSON is an export record; it cannot reopen a scenario in this version.

## Find the right guide

[Documentation index](docs/README.md) groups the analyst, methods and developer guides. Start with [sharing and recovery](docs/exchange-recovery.md) before handing work to a colleague, and read [local data and privacy](docs/privacy-recovery.md) before using sensitive data.

Developers can use [architecture and checks](docs/architecture.md), [JSON contracts](docs/data-contract.md), [contributing](CONTRIBUTING.md), [security](SECURITY.md) and [third-party notices](THIRD_PARTY.md). [Platform/accessibility status](docs/accessibility-platforms.md) and [DPG evidence](docs/dpg-evidence.md) distinguish implementation from remaining acceptance work.

## Ownership and contributions

Copyright 2026 Teal Insights. The application is permissively licensed open source under the [MIT license](LICENSE). Workbook, dependency and font rights are separate. No institutional endorsement is implied.

For a defect report, provide the app version, operating system, steps and a non-sensitive description. Review any material before placing it in a public issue. Workbooks, databases, journals, screenshots and logs may disclose analytical or personal data. Consult [security reporting](SECURITY.md) for current reporting arrangements.
