# Security and sensitive reports

This preview supports a single user running a local loopback service. It has no multi-user authentication or tenant isolation. Keep it off public proxies and shared servers. Analytical workspaces contain workbooks, saved assumptions, private journals and shared explanations. The app does not encrypt them.

## Reporting status

A maintained private vulnerability-reporting route and supported-version policy have not yet been established. Do not send a sensitive report to an invented or unverified address. Enabling and testing a private route, assigning a responsible maintainer and agreeing response procedures remain general-release requirements.

Before release, the repository administrator should enable and test [GitHub private vulnerability reporting](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository), verify that maintainers receive notifications, and publish the confirmed route here. Set supported versions, triage responsibility, disclosure coordination and response expectations only after maintainers accept them. An enabled setting alone does not prove a report will be read.

For a non-sensitive public bug report, supply the exact source/release identity and a minimal synthetic reproducer. Do not attach a workbook, database, journal, diagnostic log, screenshot, token or exploit containing private data. Public issues are unsuitable for confidential evidence. Follow your organisation's incident procedures for an actual disclosure.

## Implemented local safeguards and limits

The local service checks the Host header, validates a request token and allowed Origin for protected routes, bounds request and workbook-archive size, and sends no-store and content-security headers. Workbook intake does not execute macros or refresh external links. These measures do not establish a completed security or network audit. Another process with access to the same user account may read local files or use the local service.

Exports select fields explicitly. Private journals, internal scenario names and original filenames are excluded from the comparison export. Shared explanations and chart labels are included where documented and may contain sensitive information. Inspect downloads before sharing. Hashes identify files and do not anonymise them.

For a suspected local failure, stop using the affected workspace and retain an untouched private copy. Record the version and non-sensitive reproduction steps. See [privacy and recovery](docs/privacy-recovery.md) for storage and backup limits.

## Hosted and collaboration changes

A hosted calculator requires a separate security review. It must enforce its input scope on the server, isolate visitor state and exports, bound resources, expire/delete visitor data and explain server-side processing. No hosted security acceptance is claimed here. Contributor interaction also needs a conduct policy, confidential escalation and moderation responsibility before public support channels are relied upon.

Source publication controls are described in [release controls](docs/release-controls.md). Confidential fixtures, analytical data and private history must remain outside public source, build contexts and release assets.
