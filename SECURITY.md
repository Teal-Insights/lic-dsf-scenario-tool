# Security and sensitive reports

This preview supports a single user running a local loopback service. It has no multi-user authentication or tenant isolation. Keep it off public proxies and shared servers. Analytical workspaces contain workbooks, saved assumptions, private journals and shared explanations. The app does not encrypt them.

## Report a suspected vulnerability privately

Use [GitHub private vulnerability reporting](https://github.com/Teal-Insights/lic-dsf-scenario-tool/security/advisories/new). This setting was enabled and read back on 13 September 2026. Do not put exploit details, tokens or confidential analytical material in a public issue.

Teal Insights owns security triage for this experimental preview. Support is best-effort, with no guaranteed response time or continuous monitoring. A recurring review routine is being arranged; enabling the GitHub setting alone does not verify notification delivery or timely review.

If you cannot use GitHub, email [lte@tealinsights.com](mailto:lte@tealinsights.com?subject=LIC-DSF%20private%20security%20report) with a minimal initial description and a way to reply. Do not attach confidential workbooks, credentials, sensitive logs or weaponized examples to that first message. Agree an appropriate channel for sensitive evidence before sending it. Email is a contact fallback, not a claim of a specially secured reporting service.

Include the application release, operating system, affected feature, likely impact and minimal reproduction steps using synthetic or official illustrative data where possible. We may ask for more information privately. We will assess credible reports, coordinate fixes and disclosure with reporters, and publish an advisory when appropriate; none of those steps has a guaranteed turnaround.

## Supported versions and updates

The first experimental release is `0.1.0-alpha.1` (Python package `0.1.0a1`). Report problems with the exact release you used. We intend to fix supported issues in the latest preview; older previews have no promised backports or long-term support. There is no automatic updater. Review release notes and back up local work before replacing the package. Unreleased development builds are not an additional supported distribution.

For a non-sensitive public bug report, supply the exact source/release identity and a minimal synthetic reproducer. Do not attach a workbook, database, journal, diagnostic log, screenshot, token or exploit containing private data. Public issues are unsuitable for confidential evidence. Follow your organisation's incident procedures for an actual disclosure.

## Implemented local safeguards and limits

The local service checks the Host header, validates a request token and allowed Origin for protected routes, bounds request and workbook-archive size, and sends no-store and content-security headers. Workbook intake does not execute macros or refresh external links. These measures do not establish a completed security or network audit. Loopback is shared by the host, not isolated to one operating-system account. Any process able to reach this host's loopback service can obtain its boot token and use its APIs, including a process belonging to another local account. Host/origin/token checks protect the browser request boundary; they are not OS-user authentication. Use this preview on a trusted single-user computer, not a shared host with untrusted local users or processes. Local file permissions remain a separate control.

Exports select fields explicitly. Private journals, internal scenario names and original filenames are excluded from the comparison export. Shared explanations and chart labels are included where documented and may contain sensitive information. Inspect downloads before sharing. Hashes identify files and do not anonymise them.

For a suspected local failure, stop using the affected workspace and retain an untouched private copy. Record the version and non-sensitive reproduction steps. See [privacy and recovery](docs/privacy-recovery.md) for storage and backup limits.

## Hosted and collaboration changes

A hosted calculator requires a separate security review. It must enforce its input scope on the server, isolate visitor state and exports, bound resources, expire/delete visitor data and explain server-side processing. No hosted security acceptance is claimed here. Contributor interaction also needs a conduct policy, confidential escalation and moderation responsibility before public support channels are relied upon.

Source publication controls are described in [release controls](docs/release-controls.md). Confidential fixtures, analytical data and private history must remain outside public source, build contexts and release assets.
