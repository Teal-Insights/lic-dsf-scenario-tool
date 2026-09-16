# LIC-DSF Scenario Analysis Tool

Explore how alternative macroeconomic and financing assumptions change debt indicators in a supported World Bank LIC-DSF workbook. Save separate scenarios and their explanations, compare the results and export a briefing with charts and underlying data.

**Early-stage alpha, developed iteratively.** We welcome co-design with ministries of finance, international financial institutions and other stakeholders. This is not an official IMF or World Bank product. A successful calculation is not independent fresh Excel verification, which remains pending.

## Start here

- [Documentation and walkthroughs](https://teal-insights.github.io/lic-dsf-scenario-tool/)
- [Releases: Windows and Mac downloads](https://github.com/Teal-Insights/lic-dsf-scenario-tool/releases)
- [Installation guide](docs/installation.md) and [first scenario walkthrough](docs/tutorial.md)
- [Information you can forward to IT](docs/it-review.md)
- [Methods and limits](docs/methodology.md), [verification and reproducible checks](docs/verification.md)

Use the assets attached to the alpha release page; if no downloads are listed, the preview is not yet available. Desktop packages include Python and dependencies. The initial packages target Windows x64 and Apple Silicon/macOS 14+. The Mac wrapper is unsigned and unnotarized. See [platform evidence](docs/accessibility-platforms.md) for the distinction between earlier tests and final-package acceptance. Technical users can also [install from source](docs/source-installation.md).

## Try the built-in walkthrough

**Version `0.1.0a2`.** This guide describes the alpha.2 built-in walkthrough; the earlier alpha.1 release predates this route. Check the release page for the alpha.2 desktop packages and use the assets attached to the matching release. Package-assembly status: Windows execution, downloaded Mac approval and the complete desktop walkthrough are unverified in this guide. See the [release notes](docs/release-notes-0.1.0a2.md#release-evidence) for scope and how to find later evidence for the exact download.

Select **Download and try the official example** to obtain and check the World Bank template automatically. Internet is needed once; the verified local copy can then be used offline. No private workbook or scenario inputs are sent to the publisher. In **Try an illustrative investment**, load **No investment**, **Larger assumed benefit** and **Smaller assumed benefit** one at a time, review, save and calculate. No workbook chooser or JSON import is needed. Follow the [illustrative walkthrough](docs/tutorial.md).

## From workbook to briefing

| Step | What you do |
| --- | --- |
| 1. Choose workbook | Start the official illustrative example, or choose your own completed supported workbook. |
| 2. Check baseline | Review projection years, source identity and the baseline saved in your workbook. |
| 3. Create scenarios | Edit annual assumptions, explain changes, save revisions and calculate. |
| 4. Compare | Select calculated cases and choose the case against which differences should be measured. |
| 5. Export briefing | Review both chart views, edit titles beside the charts and download the complete packet. |

The app runs in your browser on your own computer. A pinned Python evaluator reads the supported workbook formulas deterministically; it does not use AI inference or random sampling. Installed Excel is not required for calculation. VBA macros do not run and external workbook links do not refresh.

The supported [World Bank template](docs/template-source.md) contains Ghana-labelled **purely illustrative** data. Those figures are not an official Ghana forecast or DSA. The workbook binary is supplied separately, and the application's license does not grant rights to it. Users can upload their own completed workbook in the supported format; arbitrary template versions are not supported.

## What you can explore and share

The editor covers 13 customized-scenario macro inputs over a 21-year horizon, plus supported external financing terms. Nearby help explains units and signs. Changes are adjustments to the workbook's assumptions: zero means no adjustment; a blank is unfinished. Financing rates appear as percentages.

Generic growth, funding-cost and investment exercises provide editable illustrative assumptions. They are teaching examples, not calibrated forecasts or estimated investment returns. The workbook reference baseline and a calculated zero-adjustment customized case can differ; choose a control that isolates the change you want to study.

Both **Standard LIC-DSF** and **Policy briefing** charts appear together and use the same numerical record. Output indicators cover six reported years. Lines between observations do not establish annual peaks or first threshold-crossing dates. CSV/JSON preserve full precision; chart labels are rounded for reading.

A complete briefing ZIP contains two PDF reports, twelve PNG and twelve SVG charts, five CSV tables, an Excel workbook, full-precision comparison JSON and a file-fingerprint manifest. Reports and tables explain source, assumptions, shared reasoning and evidence. Shared explanations and chart labels are intentional; private journals, internal workspace names and the original workbook are excluded. Review the actual files before sharing, because deliberately shared text and assumptions may still be confidential.

For optional advanced exchange, a separate [scenario file](docs/exchange-recovery.md) lets a colleague import one case's inputs for the identical workbook, then review, save and calculate a new draft. It does not import verified results. Cross-workbook translation and multi-case exchange are not implemented. A briefing packet, a scenario file and a private backup serve different purposes.

## Evidence, safety and contribution

[Verification](docs/verification.md) distinguishes file identity, supported structure, saved-cache consistency, application regression, cross-platform agreement and fresh Excel comparison. The repository includes reproducible tests and a scoped official-example regression reference. Published CI results and exact package evidence must identify the build actually tested.

The alpha.2 source preserves the exact built-in teaching-resource bytes during Git checkout, including with Windows-style line-ending conversion. See the [resource-integrity checks](docs/verification.md#teaching-resource-checkout-integrity) for the reproduction and its limits.

Use this single-user preview on a trusted desktop. Its loopback browser service is not operating-system account authentication; it is unsuitable for a shared host with untrusted concurrent local users or processes. [Security](SECURITY.md), [privacy and recovery](docs/privacy-recovery.md) and [IT information](docs/it-review.md) explain the actual boundaries. No security certification or unconditional no-egress guarantee is claimed.

We use the [Digital Public Goods Standard assessment](docs/dpg-evidence.md) to document practical alignment, evidence, gaps and technical choices. The tool has not been formally recognized or certified and does not claim full compliance.

We welcome focused [contributions](CONTRIBUTING.md) under maintainer roadmap control, with accountable review and meaningful validation, including for AI-assisted work. Follow the [conduct policy](CODE_OF_CONDUCT.md). Report suspected vulnerabilities privately through [the security route](SECURITY.md), not public issues.

## Ownership and feedback

Copyright 2026 Teal Insights. Application code is open source under the [MIT license](LICENSE). [Third-party notices](THIRD_PARTY.md) distinguish dependency, font and workbook rights. No stakeholder endorsement is implied.

[Help shape the next version](docs/feedback.md), or email [lte@tealinsights.com](mailto:lte@tealinsights.com). Describe what you tried and what would improve your work. Please leave confidential workbooks, analytical data, credentials and private logs out of feedback. Support is best-effort, without a guaranteed response time.
