# Local calculation for ministries and IT

Forward this page to a ministry or an IT department. It explains data confidentiality for a browser-based LIC-DSF calculator: the analyst’s workbook is not uploaded for calculation. Whether the software can change after review is a separate question. This note does not claim a security certification, report a completed network audit, or select a delivery architecture.

The wording follows [local data and recovery](privacy-recovery.md), [information for IT departments](it-review.md), and the [publication boundary](privacy-and-publication.md).

## Claim

Calculation runs on the analyst’s computer. Teal Insights does not receive the workbook or results by default.

## What stays on the analyst’s computer

The analyst chooses a workbook with the browser’s file picker. The page reads that file in the tab and calculates there. There is no required calculation account, and there is no hosted upload of the workbook for calculation. Saved scenarios and the workbook copy stay in the browser profile for that address. Clearing that site’s data removes them. Charts, briefing packets, and scenario files are downloads on the analyst’s computer. The analyst chooses whether to send a downloaded file.

On the public in-browser application at `https://d3iptw2fvdc3fp.cloudfront.net/`, the page answers its calculation routes in the tab. The site supplies the page, scripts, wheels, fonts, and the checked official template. The first visit also downloads the Python runtime from jsDelivr. Those requests carry application files and the published template. They do not carry the analyst’s workbook, scenarios, or results. The desktop application calculates through a loopback service on the same computer; [information for IT departments](it-review.md) describes that route, its package, and its signing limits.

The illustrative hosted pilot is a different service. It is not the calculator in the claim above. Its own description states its server boundary, visit lifetime, and refusal of workbook upload.

## Limits

Choosing a file lets that page read it. The application keeps the copy in the browser profile for the site address and does not upload that copy for calculation.

Browser extensions, cloud-sync software, operating-system backups, and email are outside the application. A browser profile or download folder that another product syncs is no longer only local. Sending a briefing or a workbook by email is the sender’s action. The application provides no workspace encryption, remote wipe, or secure erasure. Operating-system permissions, disk encryption, backups, and endpoint controls remain the institution’s responsibility.

A live web address is a separate integrity problem. The bytes the browser runs can change after someone has reviewed them. The current public address reuses paths: replacing the files at those paths changes what a later visit runs, and the cache policy can also keep an older response. The companion note on the delivery path covers that integrity question. This page does not select a delivery architecture, and this repository does not yet contain that companion note.

These design choices do not constitute a completed network or security audit. No security certification is claimed. Loading the page, the Python runtime, or the official template uses the network. CloudFront, jsDelivr, or the template publisher can see ordinary connection information, such as an IP address, for those requests. The application does not require a telemetry service. Browser software, extensions, and the institution’s own endpoint tools have their own network behavior. Do not read this note as an unconditional no-egress guarantee.

Deliberately shared explanations and downloaded briefings can still contain confidential information. Review the actual file before sending it. An export does not anonymise the economics. Values, years, labels, and file hashes may identify a source or analysis.

## Terms of service and privacy policy

Before production use, the ministry-facing page must link both a Terms of Service and a Privacy Policy. The links must use the same origin as that page, or an agreed institutional host.

The Privacy Policy must state:

- whether workbook bytes, scenarios, results, or diagnostics leave the device
- what connection metadata a publisher or CDN may see if any network fetch remains
- the retention period if any temporary server path exists
- that deliberate exports are the user’s responsibility

The Terms of Service must cover:

- acceptable use
- that outputs are not an official DSA
- liability limits appropriate to Teal Insights’ counsel
- that updates replace a reviewed build rather than silently rewriting a live page when the frozen-delivery path is in use

This note is not those documents. It does not contain their legal text.

| Role | Record |
| --- | --- |
| Drafter | Teal Insights drafts the Privacy Policy and Terms of Service. This note records the requirement. |
| Review | A maintainer reviews the draft against this note. Counsel reviews it when Teal Insights’ counsel requires that review. Publication waits for the counsel-approved copy when that review is required. |
| Canonical URLs | Not yet assigned. They will be recorded on the drafting task and linked from the ministry-facing page: same origin, or an agreed institutional host. |
| Drafting task | [Draft Privacy Policy and Terms of Service](https://github.com/Teal-Insights/lic-dsf-scenario-tool/issues/22). Link or attach the counsel-approved copy there. |

The current public address is an early-stage preview. Publishing this note does not make that address a production ministry service, and it does not supply the missing Privacy Policy or Terms of Service.

[Documentation index](README.md) · [Local data and recovery](privacy-recovery.md) · [Information for IT departments](it-review.md)
