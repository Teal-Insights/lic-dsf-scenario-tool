# Local data, sharing and recovery

The application reads an uploaded workbook and keeps a separate copy in the chosen data directory. It stores scenarios, results and journal entries locally. The original selected file is not overwritten. The local service binds to `127.0.0.1`; it has no hosted upload service or account system. These design choices do not constitute a completed network or security audit.

## Know what is retained

| Location | Contents |
| --- | --- |
| `workbooks/` in your data directory | Copies of accepted workbooks, named by content hash |
| `scenarios.sqlite3` | Workbook labels, outward chart context, scenario revisions, deliberately shared explanations, results and private reasoning |
| `jobs/` | Calculation requests, outputs and diagnostic logs |
| Browser and download folder | Unsaved drafts, previews and files you download |

The workspace is not application-encrypted. Operating-system access controls, device encryption, backups and any cloud-sync policy remain your responsibility. Other people with access to your account or data folder may be able to read it. The local HTTP service is not intended for untrusted users sharing one operating-system account or for exposure through a proxy or public address.

## Review a shareable export

PDF/PNG charts use your shared scenario labels, the separately saved optional chart-context label and a workbook hash prefix. JSON includes those labels and the context revision plus assumptions, results, full workbook/scenario identities, source cells and evidence. Internal scenario names, original workbook filenames and journal entries are excluded by the application's selected export fields. This does **not** anonymise the economics: values, years, labels and file hashes may identify a source or analysis.

Check the actual downloaded file and its metadata before sending it. Keep evidence and any illustrative-data disclosure attached. Do not share the whole workspace as if it were a chart export. The preview has no GUI internal-pack export or spreadsheet export; a private full-workspace backup is a different operation.

Do not attach analytical data, journals, logs or screenshots to public support issues. Report a reproducible, non-sensitive description first. A formal private vulnerability-reporting route and independently reviewed privacy/security assessment remain release gaps.

## Back up and restore

1. Save scenario edits and journal entries separately. Wait until calculations finish.
2. Stop the application. Copy the **entire data directory** to a new private backup location, without overwriting an older backup.
3. To restore, keep the current directory intact. Copy the backup to a new directory and start the same application version with `--data-dir` pointing there.
4. Reopen the workbook and inspect the current saved revision and the journal history. Recalculate if the runtime changed. Compare any important restored export with the retained original.

Copying only the database omits uploaded workbooks and job artifacts. The store has a database-backup API, but the browser does not expose a complete workspace backup/restore control. Recovery acceptance remains tied to the released package and actual platform. Before upgrading a workspace from schema 1 or 2 to schema 3, keep a stopped copy: shared-explanation metadata is added without rewriting historical scenario, result or private-journal rows, but older applications cannot open the upgraded version. Historical revisions receive empty shared explanations. Roll back using the preserved copy and compatible application, not by editing the version number.

## If something stops working

| Symptom | Action |
| --- | --- |
| Unsupported workbook | Keep the original. Read the reported structure findings; do not rename sheets or remove formulas merely to bypass checks. |
| Empty input or invalid terms | Complete the named field with a finite number. Use zero only if no adjustment is intended. Check whole-year grace/maturity. |
| Calculation failed or timed out | Saved inputs remain. Read the message, check assumptions, and retry only after understanding the failure. A failure is not a zero result. |
| Application restarted during calculation | Reopen the saved scenario and calculate again. A missing job status does not prove a result completed. |
| Result stale | Save and calculate the current revision with the current runtime before export. Older records are retained separately. |
| Local workbook missing or changed | Re-upload the original exact file. Do not silently substitute a re-saved or edited copy. |
| Workspace schema version rejected | Keep an untouched backup and use the compatible application version. Supported migrations are schemas 1 and 2 to schema 3; unknown versions are not rewritten. |
| Port already in use | Start with another unused `--port`; use its printed loopback address. |

Closing the browser can lose unsaved drafts. A saved journal entry is durable; text still in its editor is not. The preview has no deletion interface or retention scheduler. To remove a workspace, stop the application and deliberately delete its data directory and relevant backups/downloads under your organisation's retention policy. Ordinary deletion does not guarantee forensic erasure.

Shared per-input explanations are intentionally included in PDF annexes and comparison-v3 JSON. They are separate from the private journal, which remains excluded. Review those explanations and assumptions before sending them; an export can be sensitive even though workbook contents and private journals are absent.

## Network and future hosted use

The inspected local server uses a local HTML interface and loopback requests. Dependency installation and obtaining the official template can require external network access. No complete measured offline/network audit is claimed. Cloud-sync software, browser extensions and operating-system backups can create additional copies outside the application's control.

A future online calculator will process visitor assumptions on its server. Its retention period, deletion behavior, operator access, infrastructure logs and privacy notice must be specified and tested before launch. Local storage assurances do not describe a hosted deployment. Keep confidential workbooks and assumptions out of an unreviewed online service.
