# Labels and workbook identity on shared charts

In step 2, **Check baseline**, **Label for shared charts** is optional text you deliberately choose to show outside your workspace. Save the label before comparing or exporting. Leave it blank to show only the workbook identifier. A label is saved separately for each exact workbook; changing sources loads that source’s own label or a blank field.

The label appears on both PNG views and every PDF page. Each page also shows the first 12 characters of the workbook’s SHA-256; the full identity remains in the JSON. This short reference identifies bytes conveniently. It is not an assurance of calculation accuracy, provenance or institutional endorsement, and it is never used to look up a workbook.

## Write the label deliberately

Use up to 80 characters of plain, single-line text. Fiscal years such as `Budget: FY2030/31` are supported. Paths, links, artifact filenames and hidden/control characters are refused. Use a dash for other slash-separated prose. Accents and ordinary punctuation are preserved; mathematical notation is displayed literally. Chart export checks whether its bundled font can display the label. If a character is unsupported, export stops with a clear message; edit the label to supported text and save it before retrying.

The application never creates this label from your workbook filename, internal scenario names, private journal or application edition note. Enter only text you intend to share. A general text validator cannot determine whether an otherwise ordinary phrase is confidential. Shared scenario labels are separate and retain their existing 40-character and path restrictions.

## Save, clear and switch safely

**Save label** commits the outward text. **Discard label** loads the latest saved label from the workspace, including changes made in another tab. A blank saved label is an explicit clear and is retained; configured starting labels cannot silently restore it later. Unsaved label edits block comparison, export and source switching until saved or discarded. They do not change scenario inputs or require a fresh calculation.

A change made in another application tab can make your loaded label out of date. The application refuses an export using that old revision and retains your draft. If you want to keep your draft text, copy it first. Choose **Discard label** to inspect the latest saved label, then deliberately reapply and save any intended edit. A previously displayed chart is not permission to export unseen new text.

The original illustrative-data disclosure, evidence status and comparison scope remain visible regardless of the label. Keep the data-and-assumptions JSON with a briefing: a chart label alone does not contain its full numerical assumptions. See [the JSON contract](data-contract.md) and [privacy and recovery](privacy-recovery.md).
