# Share a briefing and recover saved work

Use PDF/PNG and comparison JSON to share selected results. Use a stopped copy of the complete data directory to preserve the editable workspace. These operations have different contents and purposes.

[Documentation index](README.md) · [Local data and privacy](privacy-recovery.md) · [JSON contract](data-contract.md)

## Hand a colleague a reviewable result

1. Select calculated cases from one workbook and choose the comparator. Use clear, distinct shared scenario labels.
2. Review the optional shared chart heading and per-input explanations. They are deliberately included in outward files.
3. Download the preferred chart PDF and its **data and assumptions** JSON companion. Add PNG if the recipient needs an image. The app suggests distinct `scenario-comparison-standard` and `scenario-comparison-policy` chart filenames. The JSON companion is `scenario-comparison-data.json` and contains comparison data shared by both views.
4. Open the actual downloaded files. Check the source reference, selected cases, comparator, years, units, disclosures and evidence status.
5. Explain the question the comparison addresses and its limitations when you share the files yourself.

The JSON preserves full numerical precision and input paths. A chart alone cannot reconstruct every annual assumption. Both chart styles use the same calculations, and PDF explanations describe assumptions rather than establishing causality.

This version exports `lic-dsf-comparison-v3`. It does **not** import that file back into the app. A scenario schema in the repository describes data shape; it does not provide a scenario-file exchange feature. Exact-workbook replay and applying assumptions to another workbook are pending product work. Do not promise a colleague an import button.

To continue an analysis now, reopen the original local workspace. A colleague with an authorized copy of the same workbook can manually enter the documented assumptions, save and calculate their own cases, and check the resulting identities and evidence. That is manual reproduction. Merely matching scenario names or years does not establish exact replay, and a different workbook hash identifies a different analytical basis.

## Back up and restore a workspace

Follow the authoritative [local retention and recovery guide](privacy-recovery.md). The operational steps are:

1. Save scenario and shared-explanation edits. Save private journal drafts separately. Wait for calculations to finish.
2. Stop the app with Ctrl+C in its terminal. Keep the terminal's `--data-dir` location recorded privately.
3. Copy that **entire folder** to a new private backup location using your file manager. Include `workbooks/`, `scenarios.sqlite3` and `jobs/`. Do not overwrite an earlier backup.
4. To test restoration, copy the backup to another new directory. Keep the original workspace intact.
5. Start the same installed app with the new path: `python -m lic_dsf.app --data-dir "/absolute/path/to/restored-workspace" --port 0`.
6. Open the printed local address. Reopen the workbook, inspect both saved cases and explanations, and compare them again. Check private journal entries if you use them. Compare an important downloaded export against the retained original.

`--port 0` selects an available loopback port. On Windows, use a quoted Windows path, such as `"C:\LocalDSF\restored-workspace"`. Actual Windows operation remains separately unverified.

A database-only copy omits workbook and job files. A copy taken while the app writes is outside this documented cold-backup procedure. Browser-only drafts, downloaded files in other folders and the installed runtime are not captured by the workspace copy. Keep important downloaded files and the exact reviewed application distribution alongside your records under appropriate access controls.

## Upgrade or recover after interruption

Before an upgrade, retain a stopped backup and the compatible application. Known workspace schemas 1 and 2 migrate to schema 3 by adding metadata; private journals are not converted into shared explanations. Older applications cannot open schema 3. Restore the preserved copy to roll back; do not edit the schema number.

After a calculation is interrupted, reopen the saved scenario and calculate it again. A missing job status is not evidence that calculation finished. Changed numerical inputs or financing terms require calculation before comparison/export. A revision that changes only the name, legend label or shared explanations can keep an already-current calculation. Returning to an earlier numerical definition after an intervening change still requires calculation. An upgraded runtime with a different calculation identity also requires a new run, even if the scenario itself is unchanged. Keep the older result and its original evidence; do not relabel it as a calculation performed by the new runtime.

If a saved workbook copy is missing or altered, re-upload the exact original. A re-saved workbook has a new hash and should be treated as a new source. For unsupported input, stale results and other messages, use the [troubleshooting table](privacy-recovery.md#if-something-stops-working).

Full-workspace backups can include sensitive workbook data and private notes. They are not briefing exports. Consult the privacy guide before copying them to shared or synchronized folders.
