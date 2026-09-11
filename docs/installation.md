# Install and run the source preview

This is the source-install route for a technical maintainer. If a maintainer has already installed the app, use the supplied local launch shortcut and continue to [the tutorial](tutorial.md). That shortcut opens the existing installation on that computer. A portable click-only installer and actual Windows acceptance remain separate work.

The technical checks below distinguish an earlier clean dependency installation from subsequent installed-browser checks. A final distributed package still needs evidence for its own exact contents and supported platforms.

You need Python 3.11 or later, Git for the pinned evaluator dependency, and a modern browser. The minimum Python declaration does not establish that every Python/platform combination supports all pinned dependencies. Installation downloads dependencies; running the app is a separate activity. An offline dependency bundle has not been accepted.

## Install

Obtain a reviewed source distribution and open a terminal in its root, where `pyproject.toml` and LICENSE are located. Before creating an environment, select an installed Python interpreter. Python 3.11 is the currently exercised version family; other declared-compatible versions still need their own dependency and platform checks.

On macOS or Linux, check the available interpreter:

```sh
python3 --version
```

If it reports the version you intend to test, create the environment with the same command:

```sh
python3 -m venv .venv
source .venv/bin/activate
```

If your Python 3.11 installation instead uses `python3.11` or a full executable path, use that command in both the version check and environment creation. If no suitable interpreter is installed, install Python first; do not assume the unversioned `python` command exists before activation.

On Windows Command Prompt, select an installed Python 3.11 with the Python launcher:

```bat
py -3.11 --version
py -3.11 -m venv .venv
.venv\Scripts\activate.bat
```

If `py` is unavailable, use the full path to the intended Python executable instead, quoting a path that contains spaces. These are source-install instructions, not a claim of tested Windows operation. After activation, `python --version` should identify the selected environment; the commands below use that environment's `python`.

Install the distribution without editable mode:

```sh
python -m pip install .
python -m lic_dsf.app --help
```

If dependency resolution or the help command fails, retain the error and stop. Do not substitute an unpinned evaluator or modify the workbook to make the install pass. A maintainer must resolve the packaging discrepancy before this route can be called reproducible.

## Start a workspace

Choose a persistent data folder **outside the source tree and installed package**, under your control and away from unintended cloud sync. Replace the example folder below with that location:

```sh
python -m lic_dsf.app --data-dir /absolute/path/to/local-workspace --port 8526
```

Windows uses a Windows path, for example `C:\LocalDSF\workspace`. Open the printed address, normally `http://127.0.0.1:8526`. Leave the terminal running. The service binds to the local computer's loopback address; it is not a multi-user hosted server. If the port is occupied, choose another unused port with `--port`, or pass `--port 0` to let the operating system choose one and open the printed address.

Upload a workbook in the browser. No example file is required to start. To provide the optional official illustrative-example button, download the original template separately and add `--example /absolute/path/to/template.xlsm --illustrative-example` to the start command. The app checks the configured example against the recorded official hash. Do not disable that check to use an edited copy; upload a supported copy through the normal route instead.

## Stop and reopen

Save scenario and journal drafts. Wait for the current calculation to finish, then press Ctrl+C in the terminal. Start again using the same data directory and reopen your workbook in the workspace selector. Browser-only unsaved edits are not a backup. See [exchange and recovery](exchange-recovery.md) for interruption and backup instructions.

## Verify your installation

An independent tester must install into an empty environment using only the reviewed source and public dependencies, open the packaged browser page, complete the tutorial, export both chart views, stop, restart and reopen the saved work. Record the exact package and dependency identities, platform, browser and results. A successful `--help` call alone is insufficient.

## If installation fails

| Symptom | What to check |
| --- | --- |
| Python command missing | Use the full path to an installed supported interpreter for both version check and environment creation. |
| Git missing or evaluator fetch fails | The evaluator dependency is pinned to a public Git commit. Check Git and network access. Do not replace the pin with a different package. |
| Dependency resolution or download failure | Check connectivity and whether the selected Python/platform has compatible pinned dependencies. Retain the error; a missing download does not establish a source-code defect. |
| Browser connection refused | Keep the app terminal running and use the exact printed address and port. |
| Old interface after changing source | A noneditable installation keeps its installed copy. Reinstall the reviewed source, restart the app and reload the browser. |

`python -m pip check` verifies installed dependency requirements. To see the package actually imported, run `python -c "import lic_dsf; print(lic_dsf.__file__)"`. It should point inside the activated environment, not another checkout. Neither check proves numerical correctness.

[Documentation index](README.md) · [Continue to the worked tutorial](tutorial.md)

## Recorded technical walkthrough

An earlier September 11, 2026 build (calculation-core fingerprint beginning `3efc35bb55b8`) was installed noneditably in a new Python 3.11.15 environment on macOS arm64, fetched the pinned evaluator commit, passed `pip check` and completed the two-case tutorial through sandboxed headless Chrome 152. Both cases matched 76/76 selected saved-workbook checks, with 36 output observations per case and fresh Excel verification pending. Both PDF/PNG views and comparison-v3 JSON downloaded. A stopped copy restored both calculated cases, shared explanations and the chart heading without recalculation; its JSON and standard PDF exports were byte-identical.

This earlier clean-install and recovery evidence applies to the build tested at that time. It is a technical walkthrough on one Mac. It does not establish a new human analyst's acceptance, actual Windows/Linux operation, a fully pinned transitive dependency bundle, offline installation or fresh Excel equivalence. The source manifest, installed identities, dependency report and results must accompany any release-level use of this evidence. Recheck the installed journey after a candidate changes.

A later same-day check installed the updated package (calculation-core fingerprint beginning `b15358c637ba`) into the isolated dependency environment and used a new empty workspace. It repeated the two-case browser exercise, downloaded all five files with the new view-specific filenames, and inspected all 18 PDF pages. Heading and legend edits, followed by a shared-explanation-only save, retained both calculations with two total calculation jobs. All 72 reported point records matched the earlier exercise and each case retained 76/76 saved-cache agreement. After a stop and restart, the updated text and current calculations reopened, and the JSON matched the latest pre-restart export byte for byte.

This follow-up checks the updated installed workflow and result reuse. It does not repeat a clean dependency installation or full-workspace backup drill, and it adds no fresh Excel or Windows evidence. Earlier results remain stored under their original runtime identities; a changed calculation-core fingerprint requires a new run before current use.
