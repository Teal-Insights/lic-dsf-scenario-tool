# Labels and workbook identity on shared charts

In step 5, **Review and export a briefing**, the **Chart text** panel beside the previews holds two kinds of outward text:

- **Heading on both chart views (optional)** applies to this exact workbook. Leave this heading blank to show the workbook identifier without an added heading. Use up to 80 characters.
- **Legend label** names a saved case on both views, in the comparison table and in exports. Each label is required, has a 40-character limit, and must differ from the other saved cases' labels and from “Reference baseline”.

Apply the text before comparing or exporting. A legend change saves a new case revision and retains an already-current calculation. The heading has its own per-workbook revision. Changing sources loads that source's saved heading or a blank field.

The heading appears on both PNG views and every PDF page. Each page also shows the first 12 characters of the workbook’s SHA-256; the full identity remains in the JSON. This short reference identifies bytes conveniently. It is not an assurance of calculation accuracy, provenance or institutional endorsement, and it is never used to look up a workbook.

## Write the heading deliberately

Use up to 80 characters of plain, single-line text. Fiscal years such as `Budget: FY2030/31` are supported. Paths, links, artifact filenames and hidden/control characters are refused. Use a dash for other slash-separated prose. Accents and ordinary punctuation are preserved; mathematical notation is displayed literally. Chart export checks whether its bundled font can display the label. If a character is unsupported, export stops with a clear message; edit the label to supported text and apply it before retrying.

The application never creates this label from your workbook filename, internal scenario names, private journal or application edition note. Enter only text you intend to share. A general text validator cannot determine whether an otherwise ordinary phrase is confidential. Shared scenario labels are separate and retain their existing 40-character and path restrictions.

## Apply, clear and switch safely

**Apply to both views** commits the outward text in one operation: every proposed legend label and the heading are validated first, every case's expected revision and the heading's expected revision are checked together, and either all of it is saved or none of it. A refused apply changes nothing, keeps your typed text and can be retried. After an apply, the open case in step 3 is reloaded as one coherent snapshot (inputs, financing, explanations, revision and result state), and an unsaved private journal draft is kept. **Discard edits and keep saved text** loads the latest saved heading and labels from the workspace, including changes made in another tab, and reloads the open case the same way. Existing previews retain the saved heading while an edit is unapplied; comparison and downloads are paused. Both actions refresh the previews automatically when selected calculations are current and numerical inputs are unchanged. A blank saved heading is an explicit clear and is retained; configured starting labels cannot silently restore it later. Unsaved label edits block comparison, export and source switching until applied or the saved heading is restored. Chart-text edits do not change scenario inputs. They can reuse an already-current calculation, but cannot make an absent or stale result current.

A change made in another application tab can make your loaded label out of date. The application refuses an export using that old revision. If you have no unapplied edit, it loads the latest saved text and refreshes both views by itself, and tells you to download again. If you have an unapplied edit, it keeps your draft and asks you to choose **Discard edits and keep saved text** (copy your draft first if you want it). A previously displayed chart is not permission to export unseen new text.

The original illustrative-data disclosure, evidence status and comparison scope remain visible regardless of the label. Keep the data-and-assumptions JSON with a briefing: a chart label alone does not contain its full numerical assumptions. See [the JSON contract](data-contract.md) and [privacy and recovery](privacy-recovery.md).
