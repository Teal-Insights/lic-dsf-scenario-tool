# Contributing

Thank you for helping improve this early-stage tool. We welcome reproducible bug reports, clearer documentation, accessibility improvements and proposals grounded in an analyst's work. We are developing iteratively and welcome co-design with ministries of finance, international financial institutions and other stakeholders.

Please follow our [conduct and reporting expectations](CODE_OF_CONDUCT.md).

## Start with the problem

Maintainers set the roadmap and decide which contributions to accept. Please discuss substantial features, numerical-method changes, architecture changes and new dependencies before implementing them. Agreement that a problem matters is not a promise to merge a particular solution. Small, focused fixes are easier to assess than large rewrites.

A useful proposal explains who faces the problem, what they are trying to accomplish and a concrete example using public illustrative or neutral synthetic material. A good contribution may be declined because it adds maintenance or security costs, conflicts with the supported scope, or is not a current priority. We cannot promise to repair or complete a submission on a contributor's behalf.

## Responsibility for AI-assisted contributions

AI assistance is permitted. You remain responsible for understanding every submitted change, checking its provenance and licensing, and verifying its behavior. Explain material generated changes and how you reviewed them; do not submit private prompts or confidential source material. Never claim that a test ran when it did not, invent review evidence, or submit generated bulk changes you cannot explain.

We assess quality and evidence rather than guessing how text or code was produced. Unexplained rewrites, fabricated validation, unrelated changes and repeated low-quality submissions may be closed without detailed review. Passing automated checks does not guarantee acceptance.

## Keep submissions reviewable and safe

Use one focused pull request per problem. Explain the observed and intended behavior, the changes, relevant tests actually run, and remaining limitations. Identify new dependencies, changed network access, installation/build steps and numerical behavior explicitly. Do not weaken numerical tolerances or remove checks simply to obtain a pass.

Contributors should not include credentials, completed analytical workbooks, private logs or unlicensed material. Check SECURITY.md for the current status of private vulnerability reporting before sending a sensitive report. Do not post exploit details or confidential evidence in a public issue.

Maintainer review and the release review remain required. A contribution does not acquire merge, publishing or credential access by passing checks. Automation, dependency and installer changes need particular scrutiny. The repository's effective protections and supported contribution workflow are being prepared for this experimental release; this document does not claim that every proposed GitHub control is already enabled.

## Development and validation

This is an early source preview. Start with the README, product decisions, methodology and architecture. Preserve the upload-first workflow, original workbooks, separate reference baseline and customized scenarios, explicit comparator and honest evidence labels.

For a small defect, describe the observed behaviour, expected behaviour and steps using a synthetic example. Larger changes should explain the analyst problem before proposing an implementation. Do not submit private workbooks, journals, screenshots, logs, internal paths or prior project history through public issues or pull requests.

Use the declared runtime in an isolated environment. From the reviewed source root, with the package installed noneditably, run:

```sh
python -m unittest discover -s tests -v
python scripts/check_javascript.py
python -m pip install ruff==0.16.7
python -m ruff check src tests scripts
```

The suite includes components loaded directly from this source tree. It does not by itself verify the installed application. Check the installed package location and exact source identity separately, and exercise the installed analyst workflow. Reinstall after source changes; a noneditable installation does not automatically reflect edits. Use neutral synthetic fixtures in committed tests. Real-template calculations require separately obtained original template bytes and a retained receipt; do not substitute saved-cache agreement for fresh Excel verification.

A change should include the reason, actual behaviour, relevant validation and remaining limitations. Update the README or reference documentation when the public contract changes. Preserve full precision, comparison tolerance and spreadsheet error classes. Never change a tolerance simply to obtain a pass.

The JavaScript command runs every checked-in suite, including example definitions, comparison clarity, scenario exchange and synthetic handlers. Use Node.js 24, matching CI. These checks use neutral synthetic objects and do not start a browser, API server or workbook calculation. Real browser interaction, layout and download checks are separate. The initial Ruff gate targets implementation errors; broad formatting changes belong in a separately agreed contribution.

Export changes need tests for intended content and excluded private fields, plus inspection of actual PDF/PNG files. Interface changes need real browser checks, including unsaved edits and delayed requests. Packaging changes need clean installation, exact resource inventory, dependency notices and platform-specific testing.

Before any release, maintainers review the exact source and generated package contents, asset rights and history. Unknown or changed payloads require renewed review. Code review and a successful build are not publication approval. See SECURITY.md for reporting restrictions and the readiness documentation for outstanding acceptance work.
