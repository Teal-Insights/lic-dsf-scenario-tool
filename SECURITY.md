# Security and sensitive reports

This preview is intended for a single user running a local loopback service. Do not expose it through a public proxy or treat it as a hardened multi-user server. Workspaces contain analytical data and private reasoning and are not encrypted by the application.

Do not post a workbook, workspace database, journal, diagnostic log, screenshot, access token or exploit containing sensitive data in a public issue. A public bug report should use a reviewed synthetic reproducer and contain no sensitive attachments.

A maintained private vulnerability-reporting route and supported-version policy have not yet been established. Enabling and testing that route, identifying responsible maintainers and reviewing response procedures are release requirements. This document does not invent an unmonitored email address or promise a response time.

For an apparent local failure, stop using the affected workspace, retain a private untouched copy and record the application version and non-sensitive steps. Source preservation, recovery and privacy guidance are in the documentation. Follow your organisation's incident and data-handling procedures for any actual disclosure.

The published-source boundary is separate from runtime data privacy: no analytical workspace, confidential file or private history belongs in source, tests, build context or release assets. A filename filter alone does not establish that a payload is safe to publish.
