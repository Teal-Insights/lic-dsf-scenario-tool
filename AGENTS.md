# General public software repository

Read `README.md`, `docs/product-contract.md`, `docs/decisions.md`, and `docs/privacy-and-publication.md` before changing this repository. These are maintained product requirements, not optional background.

This repository contains general reusable software and public documentation only. Do not import private-project history, customer files, country-specific examples or plans, correspondence, analyst records, exports, logs, screenshots, caches or local provenance paths. Do not copy an existing mixed-purpose repository to seed this one.

Use only public-source fixtures with explicit provenance or independently authored neutral synthetic tests. New or changed content requires the release review, including generated artifacts and reachable history. Ignore rules do not authorize publication. Do not bypass local publication hooks or edit review receipts.

Code and history from private repositories, and any confidential workbook or data derived from one, never enter this repository or its issues, pull requests, releases, Pages or CI artifacts. If a change seems to need them, stop and ask the maintainer.

The official template is a separately supplied input. Preserve its bytes. Its embedded worked example is illustrative. Do not claim ownership of the template, present sample labels as official country data, or imply the software MIT license applies to every required external asset.

Keep upload-first operation, numbered analyst steps, template input names/units, recoverable saved work, evidence labels and documented limitations. No numerical or compatibility claim without corresponding reproducible evidence. Never relax the locked comparison tolerance to make a check pass.

Update product decisions, README, relevant user/reference documentation and validation evidence with behavior changes. Consult existing decisions before asking the user to restate them. Record unresolved questions explicitly; do not promote a preview limitation into a permanent product requirement.

## Cursor Cloud specific instructions

Login shells provide the project `python` (repository `.venv`, Python 3.12), Node.js 24, Quarto 1.8.27, and `great-docs`. CI exercises Python 3.11; this image uses Python 3.12, which meets `requires-python`. JavaScript checks spawn `python`. On a login shell, `python3` is the separate documentation virtualenv, because the documentation build invokes `python3` and needs `tinycss2` and `pygments`. `/usr/bin/python3` remains the image interpreter.

The application install is not editable. After source changes, reinstall with `.venv/bin/python -m pip install .` from the repository root. Documentation packages stay in `~/.local/share/lic-dsf-docs-venv`, separate from `.venv`. Run the documentation commands in `docs/source-installation.md` with `~/.local/share/lic-dsf-docs-venv/bin/python`. `great-docs` selects `.venv` for Quarto when that directory exists, so `.venv` also includes `pygments==2.21.0` for the documentation post-render script. `great-docs` and `quarto` are on the login `PATH`.

The local workspace listens on `http://127.0.0.1:8526`. Its data directory is `$HOME/.local/share/lic-dsf-workspace`, outside the source tree. The environment start script launches `python -m lic_dsf.app --data-dir "$HOME/.local/share/lic-dsf-workspace" --port 8526` and leaves it in the foreground. The official illustrative workbook is downloaded by the app on request; it is not part of the source tree.

From the repository root, the source checks are `python -m unittest discover -s tests -v`, `python scripts/check_javascript.py`, and `python -m ruff check src tests scripts` with Ruff 0.16.7 from `.venv`.
