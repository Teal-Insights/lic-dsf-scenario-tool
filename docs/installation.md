# Download, start and reopen the tool

**Preview guide: 0.1.0a3.** Start with the official illustrative workbook and the [walkthrough](tutorial.md). The application is developed iteratively with stakeholder feedback; it is not an official IMF or World Bank product.

**Version `0.1.0a3`.** This guide describes the built-in walkthrough in 0.1.0a3; the earlier alpha.1 release predates this route. There is no 0.1.0a3 Mac package: the alpha.2 Mac package offers the same route with slightly older wording. Use the assets attached to the matching release. Package-assembly status: Windows-side signature confirmation, final-package Windows execution and the complete desktop walkthrough are unverified in this guide. See the [release notes](release-notes-0.1.0a3.md#release-evidence) for scope and how to find later evidence for the exact download.

Download the desktop packages from the [releases page](https://github.com/Teal-Insights/lic-dsf-scenario-tool/releases). The [alpha.1 assets](https://github.com/Teal-Insights/lic-dsf-scenario-tool/releases/tag/v0.1.0-alpha.1) predate this built-in walkthrough, so use the 0.1.0a3 Windows asset or the alpha.2 Mac asset for this guide. If no matching download is listed, that package is not available yet and technical users can inspect the source through [source installation](source-installation.md). Use only assets attached to the matching release. Do not use an unrelated repository's files or the GitHub **Code → Download ZIP** button as a desktop installer.

| Your computer | Package | Limits |
| --- | --- | --- |
| Windows with an Intel or AMD 64-bit processor | Windows x64 ZIP, 0.1.0a3 | **Start LIC-DSF.exe** is signed by TEAL EMERY INC. Windows Server 2022 was tested with an earlier build. At package assembly, final-package execution and managed Windows 11 laptop testing were unverified; see the [release evidence](release-notes-0.1.0a3.md#release-evidence). Windows on Arm is not covered. |
| Mac with Apple Silicon (M1 or later), macOS 14 or later | Mac arm64 ZIP, 0.1.0a2 | Unsigned and not notarized by Apple, so the first attempt to open it is blocked and you have to approve it once. Follow the Mac steps below. At package assembly, the downloaded and quarantined approval route and a complete walkthrough of the packaged build were unverified; see the [release evidence](release-notes-0.1.0a2.md#release-evidence). Intel Macs and older macOS are not covered by this package. |
| Technical users on other configurations | [Source installation](source-installation.md) | Requires Python, Git and dependency installation; no additional platform acceptance is implied. |

Python and the calculation dependencies are included in the desktop ZIPs. You do not need to install Excel to calculate scenarios. You do need a browser. The built-in walkthrough obtains the supported official workbook directly from the publisher; your own analysis uses a workbook you supply. Downloading the package and the example for the first time requires internet access. The verified cached example and built-in teaching cases can then be used offline. Read the [IT information page](it-review.md) if you need technical details for institutional review.

## Windows

**Extract the ZIP before you open anything inside it.** Windows shows the inside of a ZIP file as though it were an ordinary folder, but the tool cannot run from that view. **Start LIC-DSF.exe** looks for the bundled runtime before it does anything else. If `runtime\python.exe` is not in the same folder as the launcher, it says that the program files are missing from the folder, names the file it could not find, gives the two usual causes and lists the extraction steps. The two usual causes are a launcher opened from inside the ZIP and a ZIP that was only partly extracted. Right-click the ZIP, choose **Extract All**, then open the folder Windows creates and start the tool from there.

1. Download the Windows x64 ZIP (`LIC-DSF-Tool-0.1.0a3-win64.zip`) from the release page. Right-click it and choose **Extract All**, then choose **Extract**. Keep the entire extracted folder together.
2. Put the folder somewhere you can write, outside an unintended cloud-synced folder. No administrator installation is intended. Organisational application controls may still block execution.
3. In the extracted folder, double-click **Start LIC-DSF.exe** (in File Explorer its Type is **Application**). A command window checks the package files, then opens your default browser; the first start can take a while. Keep the command window open while using the tool.
4. Windows will probably show **Windows protected your PC** at first, because the signature is new and has no download reputation yet. Choose **More info** and check the publisher. If the publisher is **TEAL EMERY INC.** and **Run anyway** is offered, choose it if your organisation's rules allow you to run programs you download; if you are not sure, ask your IT team first and send them the **IT-NOTE.txt** file from the extracted folder. If there is no **Run anyway** button, or Windows says your organisation has blocked the program, stop and send your IT team **IT-NOTE.txt**. If it says **Unknown publisher** or any other name, do not run it. If you opened **Start LIC-DSF (fallback).cmd**, go back and open **Start LIC-DSF.exe** instead. Otherwise this is not the signed download; download it again from the [releases page](https://github.com/Teal-Insights/lic-dsf-scenario-tool/releases).
5. Select **Download and try the official example** for your first run, then follow the [walkthrough](tutorial.md). If the example is already available, select **Try the official illustrative example**. Older builds use the [manual template download](template-source.md) and workbook chooser.

The launcher replaces the bare missing-path error with that explanation and the extraction steps. It cannot tell how the folder came to be incomplete, so it describes both usual causes rather than asserting one. Keep the extracted folder name short and leave it in a normal location such as your Downloads or Documents folder; very long folder paths can exceed the Windows path limit.

**Start LIC-DSF (fallback).cmd** is an unsigned script kept as a fallback, and Windows reports it as **Unknown publisher**. It runs the same bundled Python as **Start LIC-DSF.exe** and is not a way around a block.

Keep your own files, including workbooks, outside the extracted folder. Before it starts, the tool checks that the folder holds exactly the package files; if other files are present, it names them and asks you to move them out. Your saved work is kept separately; see [Save, stop and return later](#save-stop-and-return-later).

Only **Start LIC-DSF.exe** is signed. The bundled Python runtime and libraries keep their upstream bytes; some carry Python Software Foundation or Microsoft signatures and the rest are unsigned. **IT-NOTE.txt** in the package says what is signed and how to check it. If Windows or your institution blocks the tool, record the message and use your organisation's normal software-review process. Do not disable endpoint protection. A file checksum can confirm an exact download; it does not establish that software is safe.

## Mac

The Mac package is an unsigned preview. It carries no Apple Developer ID signature and no Apple notarization, so macOS treats it as software from a developer it cannot identify and blocks the first attempt to open it. Signing and notarization are planned for a later release. Until then, the approval steps below are the supported way to open it. They use the ordinary macOS approval screen. They never ask you to remove the quarantine marker, turn off Gatekeeper or weaken any security setting.

### Open it the first time

1. Download the Mac arm64 ZIP from the release page. In Finder, open your Downloads folder and double-click the ZIP to extract it.
2. Keep **LIC-DSF Scenario Tool.app** whole and put it somewhere you control, such as your Applications or Documents folder. Do not edit files inside the app.
3. Double-click the app. **Expect this first attempt to be refused.** macOS shows a notice saying it cannot verify the app or its developer. Choose **Done** or **Cancel**. Do not choose Move to Trash.
4. Open the Apple menu, choose **System Settings**, then **Privacy & Security** in the sidebar. Scroll down to the **Security** section near the bottom of that page.
5. A line there names **LIC-DSF Scenario Tool** and says it was blocked. Select **Open Anyway** on that line.
6. Confirm with your Mac login password, Touch ID or Apple Watch if you are asked.
7. A last dialog repeats the warning and offers **Open Anyway** or **Open**. Choose it.
8. macOS may also ask whether LIC-DSF Scenario Tool may control Terminal. Choose **OK**. The app uses Terminal only to show you that it is running and to give you a way to stop it.

For later launches, double-click the same app again. If macOS blocks it again, retain the message and follow the guidance below.

### What the screens say on each macOS version

The route is the same on every supported version; only the wording differs.

| Your macOS | The notice on the refused first attempt | The line in Privacy & Security, Security |
| --- | --- | --- |
| macOS 14, Sonoma | "LIC-DSF Scenario Tool" cannot be opened because the developer cannot be verified. | "LIC-DSF Scenario Tool" was blocked from use because it is not from an identified developer. |
| macOS 15, Sequoia | Apple could not verify "LIC-DSF Scenario Tool" is free of malware that may harm your Mac or compromise your privacy. | "LIC-DSF Scenario Tool" was blocked to protect your Mac. |
| macOS 26, Tahoe | Apple could not verify "LIC-DSF Scenario Tool" is free of malware that may harm your Mac or compromise your privacy. | "LIC-DSF Scenario Tool" was blocked to protect your Mac. |

On macOS 15 and later, holding Control and choosing Open no longer skips this approval. Use the System Settings route above.

### If Open Anyway is missing or greyed out

The **Open Anyway** line appears only for a short period after a blocked attempt. If you cannot see it, double-click the app again, dismiss the notice, and go straight back to System Settings, Privacy & Security.

If your Mac is managed by your organisation, that button can be switched off by policy. Stop there, keep a copy of the message, and use your normal software-review process. Do not try to work around the control.

### Run it and stop it

The app opens a Terminal window that shows it starting, then your default browser at a local address. Keep that Terminal window open while you work. Use **Download and try the official example**, or **Try the official illustrative example** when it is already available, then follow the [walkthrough](tutorial.md).

To stop the tool, press **Control-C** in its Terminal window, or close that window. Closing only the browser tab leaves the tool running.

A file checksum published with the release can confirm that your download is the exact file we built. It does not establish that the software is safe, and it is not a substitute for your own review.

### Mac evidence at package assembly

Earlier local copies of this application started, served the interface and quit on Apple Silicon. At package assembly, the downloaded and quarantined route through **Open Anyway** and a full walkthrough of the finished package were unverified. The steps above describe the route to follow; they do not record a successful test. Consult the [release evidence](release-notes-0.1.0a2.md#release-evidence) for later results tied to the exact archive you downloaded. If any screen differs from the table above, stop and send [feedback](feedback.md) rather than working around the control.

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
| **Start LIC-DSF.exe** says the program files are missing | The bundled runtime is not beside the launcher. Extract the whole ZIP with **Extract All**, keep every extracted file together, then run **Start LIC-DSF.exe** from the extracted folder. |
| Windows says `The system cannot find the path specified.` | An alpha.1 launcher was started from inside the ZIP. Extract the ZIP first, then run **Start LIC-DSF.exe** from the extracted folder. |
| Windows says **Unknown publisher** or a publisher other than TEAL EMERY INC. | Do not run it. If you opened **Start LIC-DSF (fallback).cmd**, open **Start LIC-DSF.exe** instead. Otherwise download the ZIP again from the releases page. |
| **Start LIC-DSF.exe** says the local workspace could not start | Double-click **Verify package.cmd**. If it says the package files match, your organisation may be blocking the bundled Python; send **IT-NOTE.txt** to your IT team. The fallback runs the same Python and is not a way around a block. |
| The tool lists files that are not part of the package | Move the named files out of the extracted folder, then start again. Keep your own files elsewhere. |
| An operating-system security warning | Retain the message; follow the approved review route. Do not weaken security settings. |
| A missing or changed package-file message | Extract a fresh complete copy. Do not edit the package manifest to make it pass. |
| A command window closes or shows an error | The launcher reports the problem before it pauses. Keep a non-confidential description of the message, any status number and your OS/architecture for feedback. |
| Browser connection refused | Check the command window is still running and use its current local address. |
| No download/example button or prepared teaching cases | Check your release version. Alpha.1 predates the built-in route; it supports manual workbook and scenario-file intake. Use the 0.1.0a3 Windows package or the alpha.2 Mac package for this walkthrough. |
| Example download fails | Check internet access and retry. A changed or corrupt publisher file is refused. Once the verified example is cached, the exercise can run offline. |
| A calculation fails | Keep the prior saved case, inspect the error, and check supported workbook/input details. Do not change verification tolerances. |

[Continue to your first scenario](tutorial.md) · [Platform evidence](accessibility-platforms.md) · [Feedback](feedback.md)
