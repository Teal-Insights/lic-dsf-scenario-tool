# Download, start and reopen the tool

**Preview guide: 0.1.0a2.** Start with the official illustrative workbook and the [walkthrough](tutorial.md). The application is developed iteratively with stakeholder feedback; it is not an official IMF or World Bank product.

**Version `0.1.0a2`.** This guide describes the alpha.2 built-in walkthrough; the earlier alpha.1 release predates this route. Check the release page for the alpha.2 desktop packages and use the assets attached to the matching release. Platform acceptance for the alpha.2 packages is not complete. See the [release notes draft](release-notes-0.1.0a2.md) for scope and the checks that remain open.

Download the desktop packages from the [releases page](https://github.com/Teal-Insights/lic-dsf-scenario-tool/releases). The [alpha.1 assets](https://github.com/Teal-Insights/lic-dsf-scenario-tool/releases/tag/v0.1.0-alpha.1) predate this built-in walkthrough, so use the alpha.2 assets for this guide. If no alpha.2 downloads are listed, that package is not available yet and technical users can inspect the source through [source installation](source-installation.md). Use only assets attached to the matching release. Do not use an unrelated repository's files or the GitHub **Code → Download ZIP** button as a desktop installer.

| Your computer | Package | Limits |
| --- | --- | --- |
| Windows with an Intel or AMD 64-bit processor | Windows x64 ZIP | Windows Server 2022 was tested with an earlier build. Final alpha execution and managed Windows 11 laptop testing remain pending. Windows on Arm is not covered. |
| Mac with Apple Silicon (M1 or later), macOS 14 or later | Mac arm64 ZIP | Unsigned and not notarized by Apple. Downloaded/quarantined Finder launch and a complete walkthrough of the next bundle remain pending. Intel Macs and older macOS are not covered by this package. |
| Technical users on other configurations | [Source installation](source-installation.md) | Requires Python, Git and dependency installation; no additional platform acceptance is implied. |

Python and the calculation dependencies are included in the desktop ZIPs. You do not need to install Excel to calculate scenarios. You do need a browser. The built-in walkthrough obtains the supported official workbook directly from the publisher; your own analysis uses a workbook you supply. Downloading the package and the example for the first time requires internet access. The verified cached example and built-in teaching cases can then be used offline. Read the [IT information page](it-review.md) if you need technical details for institutional review.

## Windows

**Extract the ZIP before you open anything inside it.** Windows shows the inside of a ZIP file as though it were an ordinary folder, but the tool cannot run from that view. From alpha.2, **Start LIC-DSF.cmd** looks for the bundled runtime before it does anything else. If `runtime\python.exe` is not in the same folder as the launcher, it says that the program files are missing from the folder, names the file it could not find, gives the two usual causes and lists the extraction steps. The two usual causes are a launcher opened from inside the ZIP and a ZIP that was only partly extracted. Right-click the ZIP, choose **Extract All**, then open the folder Windows creates and start the tool from there.

1. Download the Windows x64 ZIP from the release page. Right-click it and choose **Extract All**, then choose **Extract**. Keep the entire extracted folder together.
2. Put the folder somewhere you can write, outside an unintended cloud-synced folder. No administrator installation is intended. Organisational application controls may still block execution.
3. In the extracted folder, open **Start LIC-DSF.cmd**. A command window checks the package and opens your default browser. Keep the command window open while using the tool.
4. In alpha.2, select **Download and try the official example** for your first run, then follow the [walkthrough](tutorial.md). If the example is already available, select **Try the official illustrative example**. Older builds use the [manual template download](template-source.md) and workbook chooser.

The alpha.2 launcher replaces the bare missing-path error with that explanation and the extraction steps. It cannot tell how the folder came to be incomplete, so it describes both usual causes rather than asserting one. Keep the extracted folder name short and leave it in a normal location such as your Downloads or Documents folder; very long folder paths can exceed the Windows path limit.

The package is an unsigned preview. If Windows or your institution blocks it, record the message and use your organisation's normal software-review process. Do not disable endpoint protection. A file checksum can confirm an exact download; it does not establish that software is safe.

## Mac

1. Download the Mac arm64 ZIP from the release page and extract it in Finder.
2. Keep **LIC-DSF Scenario Tool.app** intact. Place it in a folder under your control. Do not edit files inside the app bundle.
3. Open the app. Its launcher opens Terminal, then the local interface in your default browser. Keep Terminal open while using it.
4. Use **Download and try the official example**, or **Try the official illustrative example** when already available, then follow the [walkthrough](tutorial.md). On older builds, use the [manual template download](template-source.md) and workbook chooser.

This first Mac preview has no Developer ID signature or Apple notarization. macOS may block a downloaded copy. If it does, stop and retain the message for [feedback](feedback.md) or institutional review. These instructions do not ask you to remove quarantine or turn off Gatekeeper. A successful development-machine launch would not prove that a downloaded copy passes this check.

## Save, stop and return later

Save the current scenario and any private journal edits. Wait for calculations to finish, then press **Control-C** in the app's command or Terminal window. Closing only the browser tab does not stop the local application.

To return, open the same launcher. The browser port may change; use the newly opened address. In step 1, reopen a saved workbook to retrieve its scenarios. Unsaved browser edits are not retained. See [backup and recovery](privacy-recovery.md) before moving or replacing a workspace.

| System | Saved-work location |
| --- | --- |
| Windows | `%LOCALAPPDATA%\Teal Insights\LIC-DSF Scenario Tool\workspace` |
| Mac | `~/Library/Application Support/Teal Insights/LIC-DSF Scenario Tool/workspace` |

The original selected file is preserved; the workspace contains a separate workbook copy, saved cases and other analytical records. It is outside the application package. Disk encryption, cloud sync and backups depend on your computer and folder choices.

## Update or remove

Stop the app and make a private backup before updating. Extract a new release into a separate folder rather than mixing its files with the old package. Review the new release's compatibility and migration notes. Do not run two releases against the same workspace at once. There is no automatic updater.

Deleting the extracted Windows folder or Mac app removes that copy of the software. It preserves saved work. Delete the separate data folder only if you deliberately want to remove its workbooks, scenarios, journals and caches, and have dealt with any backups or synced copies. Ordinary file deletion is not a secure-erasure guarantee.

## If something goes wrong

| What you see | Next step |
| --- | --- |
| **Start LIC-DSF.cmd** says the program files are missing | The bundled runtime is not beside the launcher. Extract the whole ZIP with **Extract All**, keep every extracted file together, then run **Start LIC-DSF.cmd** from the extracted folder. |
| Windows says `The system cannot find the path specified.` | An alpha.1 launcher was started from inside the ZIP. Extract the ZIP first, then run **Start LIC-DSF.cmd** from the extracted folder. |
| An operating-system security warning | Retain the message; follow the approved review route. Do not weaken security settings. |
| A missing or changed package-file message | Extract a fresh complete copy. Do not edit the package manifest to make it pass. |
| A command window closes or shows an error | From alpha.2 the launcher reports the status number before it pauses. Keep a non-confidential description of the message, the status number and your OS/architecture for feedback. |
| Browser connection refused | Check the command window is still running and use its current local address. |
| No download/example button or prepared teaching cases | Check your release version. Alpha.1 predates the built-in route; it supports manual workbook and scenario-file intake. Use the matching alpha.2 package for this walkthrough. |
| Example download fails | Check internet access and retry. A changed or corrupt publisher file is refused. Once the verified example is cached, the exercise can run offline. |
| A calculation fails | Keep the prior saved case, inspect the error, and check supported workbook/input details. Do not change verification tolerances. |

[Continue to your first scenario](tutorial.md) · [Platform evidence](accessibility-platforms.md) · [Feedback](feedback.md)
