# Download, start and reopen the tool

**Experimental preview: 0.1.0-alpha.1.** Start with the official illustrative workbook and the [walkthrough](tutorial.md). The application is developed iteratively with stakeholder feedback; it is not an official IMF or World Bank product.

Use the files attached to the [GitHub alpha release](https://github.com/Teal-Insights/lic-dsf-scenario-tool/releases/tag/v0.1.0-alpha.1). These instructions describe the alpha packages being prepared; the download is available only when that release is published. Do not use an unrelated repository's files or the GitHub **Code → Download ZIP** button as a desktop installer.

| Your computer | Package | Limits |
| --- | --- | --- |
| Windows with an Intel or AMD 64-bit processor | Windows x64 ZIP | Windows Server 2022 was tested with an earlier build. Final alpha execution and managed Windows 11 laptop testing remain pending. Windows on Arm is not covered. |
| Mac with Apple Silicon (M1 or later), macOS 14 or later | Mac arm64 ZIP | Unsigned and not notarized by Apple. Final Finder/download launch checks remain pending. Intel Macs and older macOS are not covered by this package. |
| Technical users on other configurations | [Source installation](source-installation.md) | Requires Python, Git and dependency installation; no additional platform acceptance is implied. |

Python and the calculation dependencies are included in the desktop ZIPs. You do not need to install Excel to calculate scenarios. You do need a browser and a separately obtained supported workbook. Downloading the package and official template requires internet access. Read the [IT information page](it-review.md) if you need technical details for institutional review.

## Windows

1. Download the Windows x64 ZIP from the release page. Right-click it and choose **Extract All**. Keep the entire extracted folder together; do not run the launcher from inside the ZIP preview.
2. Put the folder somewhere you can write, outside an unintended cloud-synced folder. No administrator installation is intended. Organisational application controls may still block execution.
3. Open **Start LIC-DSF.cmd**. A command window checks the package and opens your default browser. Keep the command window open while using the tool.
4. In the browser, choose your workbook. For a first run, use the [unchanged official example](template-source.md).

The package is an unsigned preview. If Windows or your institution blocks it, record the message and use your organisation's normal software-review process. Do not disable endpoint protection. A file checksum can confirm an exact download; it does not establish that software is safe.

## Mac

1. Download the Mac arm64 ZIP from the release page and extract it in Finder.
2. Keep **LIC-DSF Scenario Tool.app** intact. Place it in a folder under your control. Do not edit files inside the app bundle.
3. Open the app. Its launcher opens Terminal, then the local interface in your default browser. Keep Terminal open while using it.
4. Choose the [official illustrative workbook](template-source.md) in the browser.

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
| An operating-system security warning | Retain the message; follow the approved review route. Do not weaken security settings. |
| A missing or changed package-file message | Extract a fresh complete copy. Do not edit the package manifest to make it pass. |
| A command window closes or shows an error | Keep a non-confidential description of the message and your OS/architecture for feedback. |
| Browser connection refused | Check the command window is still running and use its current local address. |
| No official-example button | Download the template separately and use the workbook chooser. The desktop launch does not require a preloaded workbook. |
| A calculation fails | Keep the prior saved case, inspect the error, and check supported workbook/input details. Do not change verification tolerances. |

[Continue to your first scenario](tutorial.md) · [Platform evidence](accessibility-platforms.md) · [Feedback](feedback.md)
