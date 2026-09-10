# Install and run the source preview

This route is for a technical maintainer installing the assembled source distribution containing the calculation core, app, charts and browser page. A clean, independent installation of the final exact candidate has not yet been accepted. The click-only launch package for economists and analysts remains pending, as does an accepted Windows release. Passing this command-line route does not establish analyst-delivery acceptance.

You need Python 3.11 or later, Git for the pinned evaluator dependency, and a modern browser. The minimum Python declaration does not establish that every Python/platform combination supports all pinned dependencies. Installation downloads dependencies; running the app is a separate activity. An offline dependency bundle has not been accepted.

## Install

Obtain a reviewed source distribution and open a terminal in its root, where `pyproject.toml` and LICENSE are located. Create an isolated environment:

```sh
python -m venv .venv
```

On macOS or Linux, activate it with `source .venv/bin/activate`. On Windows Command Prompt, use `.venv\Scripts\activate.bat`. These are source-install instructions, not a claim of tested Windows operation.

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

Windows uses a Windows path, for example `C:\LocalDSF\workspace`. Open the printed address, normally `http://127.0.0.1:8526`. Leave the terminal running. The service binds to the local computer's loopback address; it is not a multi-user hosted server. If the port is occupied, choose another unused port with `--port`.

Upload a workbook in the browser. No example file is required to start. To provide the optional official illustrative-example button, download the original template separately and add `--example /absolute/path/to/template.xlsm --illustrative-example` to the start command. The app checks the configured example against the recorded official hash. Do not disable that check to use an edited copy; upload a supported copy through the normal route instead.

## Stop and reopen

Save scenario and journal drafts. Wait for the current calculation to finish, then press Ctrl+C in the terminal. Start again using the same data directory and reopen your workbook in the workspace selector. Browser-only unsaved edits are not a backup. See [recovery](privacy-recovery.md) for interruption and backup instructions.

## Installation acceptance still required

An independent tester must install into an empty environment using only the reviewed source and public dependencies, open the packaged browser page, complete the tutorial, export both chart views, stop, restart and reopen the saved work. Record the exact package and dependency identities, platform, browser and results. A successful `--help` call alone is insufficient.
