# Alpha.3 release notes

**Version `0.1.0a3`, release tag `v0.1.0-alpha.3`.** These notes describe the application and Windows package changes. Availability and acceptance are recorded with the matching release; this document does not establish either.

The interface is easier to follow. The policy view comes first, one next-step bar shows what to do next, the guidance explains Save then Calculate, the three teaching cases come first, and the wait panel and download wording are plainer. Every export carries an illustrative stamp, and chart styling and footnotes are clearer. Calculations, numerical tolerances and reported years are unchanged, and the plotted chart-data digest is pinned.

Text files are read and written as UTF-8 on every platform. The source also adds an optional [hosted walkthrough mode](hosted-pilot.md). It is not part of the Windows package, and nothing in this repository deploys it.

Known behaviour, documented rather than changed in this version: closing the browser tab does not stop the local tool (close its command window instead), and a second launch starts a second copy.

## Windows package changes

- **Signed launcher:** open **Start LIC-DSF.exe**. It is Authenticode-signed by TEAL EMERY INC. through Microsoft's Artifact Signing service, with an RFC 3161 timestamp. Only this file is signed by the publisher; the bundled Python runtime and libraries keep their upstream bytes.
- **First start:** Windows will probably show **Windows protected your PC** at first, because the identity is new and has no SmartScreen reputation yet. Check that the publisher is TEAL EMERY INC.; the [installation guide](installation.md#windows) explains the next step.
- **Fallback:** the unsigned script is now named **Start LIC-DSF (fallback).cmd**, so it is no longer confused with the signed launcher. Windows reports it as **Unknown publisher**.
- **IT note:** **IT-NOTE.txt** at the package root summarises what is signed, how to check it and how to allow the tool under AppLocker or App Control for Business.
- **Package check:** the tool says it is checking package files before it starts. It ignores the Thumbs.db and desktop.ini files that File Explorer adds. If other files are in the folder, it names them and asks you to move them out; missing or changed package files still ask for a fresh copy.
- **Manifests:** FILE-MANIFEST.json lists every file with its SHA-256. The release manifest published with the release lists every file in the ZIP, the ZIP, wheel and launcher hashes and the signing certificate's thumbprint.

The Windows helper scripts (`start_local.py` and the two `.cmd` files) are now in this repository under `packaging/windows-package/`. The signed launcher was built from `packaging/windows-bootstrap`, which is unchanged in this release.

There is no 0.1.0a3 Mac package. Mac users continue with the alpha.2 Mac package, which is unsigned and unnotarized; see the [alpha.2 notes](release-notes-0.1.0a2.md). Windows on Arm, Intel Macs and older macOS versions are not covered.

## Release evidence

**Status recorded at package assembly:** the launcher signature and its timestamp were verified on a Mac against the pinned Microsoft Identity Verification Root Certificate Authority 2020. Windows-side signature confirmation (`Get-AuthenticodeSignature` and `signtool verify`), a standard-user download and launch test, and a complete final-package browser walkthrough were unverified. Managed-laptop and ordinary-user acceptance remain unverified in this documentation.

Find `v0.1.0-alpha.3` on the [releases page](https://github.com/Teal-Insights/lic-dsf-scenario-tool/releases). If the matching release or platform asset is absent, that download is not available. Match the exact asset name and SHA-256 fingerprint against the checksums published with the release. A later test receipt must identify the release commit, application and runtime identity, OS and browser, the steps actually performed and the observed outcomes. Missing or mismatched evidence leaves the corresponding check unverified; a filename or checksum alone does not establish a test pass or software safety.

There is **no fresh Excel verification**, **no hosted security acceptance** and **no SmartScreen reputation** established here. Source tests do not establish downloaded-package launch, managed-laptop acceptance or a complete network or security assessment. The official workbook remains a separate publisher download, outside the software's MIT license.
