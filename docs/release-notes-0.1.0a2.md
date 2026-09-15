# Alpha.2 release notes draft

**Local source candidate: 0.1.0a2. Desktop bundles and publication are pending.**

The application corrections first used online are now in the source for the next desktop build. The official example can be downloaded and checked from inside the app. Three prepared teaching cases open as editable drafts, with their existing assumptions and shared explanations preserved. The larger-benefit case is labelled **Larger assumed benefit**.

Both chart previews and briefing downloads retain checks against stale comparisons. Input summaries keep small nonzero adjustments visible, discarded edits require confirmation, and packet rendering reuses text layout work within one export. Calculations, numerical tolerances and reported years are unchanged.

## Desktop packaging planned for this release

- **Windows:** extract the ZIP first. The next launcher will explain how to extract it if started without the bundled runtime, including from inside the ZIP preview. This guard still needs its Windows bundle check.
- **Mac:** the next launcher will open without a second quarantined script and retain a visible way to quit. The final bundle still needs launch and quit checks.
- **Open Anyway:** the Mac installation guide will explain System Settings, Privacy & Security, the blocked-app notice, and Open Anyway. These steps still need checking against the final unsigned bundle.

These packaging items are planned work. This source candidate does not contain desktop launchers or claim their acceptance.

## Evidence and limits

Fresh source checks are described in [verification](verification.md). Exact wheel, source archive and desktop packages each need independent review before release. Final release notes must identify the published commit, checks and asset fingerprints.

There is **no fresh Excel verification**, **no hosted security acceptance**, and **no signed desktop build** in this alpha. The Mac build remains unsigned and unnotarized. Source tests are separate from downloaded-package launch, managed-laptop acceptance and a complete network or security assessment. The official workbook remains a separate publisher download, outside the software's MIT license.
