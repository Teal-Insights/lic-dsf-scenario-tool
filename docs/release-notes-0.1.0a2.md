# Alpha.2 release notes

**Version `0.1.0a2`, release tag `v0.1.0-alpha.2`.** These notes describe the application and desktop package changes. Availability and acceptance are recorded with the matching release; this document does not establish either.

The application corrections first used online are in the alpha.2 desktop source. The official example can be downloaded and checked from inside the app. Three prepared teaching cases open as editable drafts, with their existing assumptions and shared explanations preserved. The larger-benefit case is labelled **Larger assumed benefit**.

Both chart previews and briefing downloads retain checks against stale comparisons. Input summaries keep small nonzero adjustments visible, discarded edits require confirmation, and packet rendering reuses text layout work within one export. Calculations, numerical tolerances and reported years are unchanged.

Git checkout preserves the exact built-in teaching-resource bytes under Windows-style line-ending conversion. The source archive carries the same attributes rule. Resource fingerprints and assumptions are unchanged. A local checkout/build/install reproduction is separate from Windows CI and final desktop acceptance; see [verification](verification.md#teaching-resource-checkout-integrity).

## Desktop package changes

- **Windows:** extract the whole ZIP first. If the bundled `runtime\python.exe` is missing, the launcher reports **The program files are missing from this folder.** It gives ZIP-preview launch and partial extraction as possible causes, then explains **Extract All**. This is a runtime-presence check, not proof of how the files went missing. The command window provides a visible way to stop the app.
- **Mac:** the launcher opens Terminal without a second quarantined script. Keep Terminal open while using the app and press **Control-C** to stop it. The package is unsigned and unnotarized.
- **Open Anyway:** the [installation guide](installation.md) gives the macOS 14, 15 and 26 System Settings route, including Privacy & Security and the blocked-app notice. These are instructions, not a record of a completed approval test. Do not remove quarantine, disable Gatekeeper or work around institutional controls.

Desktop launchers are distributed in the platform ZIPs; they are not part of the application wheel or this repository's source tree. Inspect the package that matches your platform. Windows on Arm, Intel Macs and older macOS versions are not covered by these packages.

## Release evidence

**Status recorded at package assembly:** final-package Windows execution, the downloaded and quarantined Mac **Open Anyway** route, and a complete final-package browser walkthrough were unverified. Earlier development-machine, Windows Server and local Mac checks establish only their recorded scope. Managed-laptop and ordinary-user acceptance remain unverified in this documentation.

Find `v0.1.0-alpha.2` on the [releases page](https://github.com/Teal-Insights/lic-dsf-scenario-tool/releases). If the matching release or platform asset is absent, that download is not available. For later test outcomes, read the evidence attached to or linked from that release and match the exact asset name and SHA-256 fingerprint against its checksums. A later receipt must identify the release commit, application/runtime identity, OS and browser, steps actually performed and observed outcomes. Missing or mismatched evidence leaves the corresponding check unverified; a filename or checksum alone does not establish a test pass or software safety.

The release commit must match the documentation bundled in both archives. Source checks, independent source/history review, package inspection and platform execution are distinct requirements. New archive bytes require renewed affected review and tests. Later test receipts can document outcomes for the frozen archive without rewriting its package-assembly status.

There is **no fresh Excel verification**, **no hosted security acceptance**, and **no signed desktop build** established here. The Mac build remains unsigned and unnotarized. Source tests do not establish downloaded-package launch, managed-laptop acceptance or a complete network or security assessment. The official workbook remains a separate publisher download, outside the software's MIT license.
