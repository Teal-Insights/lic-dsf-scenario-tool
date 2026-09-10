# Contributing

This is an early source preview. Start with the README, product decisions, methodology and architecture. Preserve the upload-first workflow, original workbooks, separate reference baseline and customized scenarios, explicit comparator and honest evidence labels.

For a small defect, describe the observed behaviour, expected behaviour and steps using a synthetic example. Larger changes should explain the analyst problem before proposing an implementation. Do not submit private workbooks, journals, screenshots, logs, internal paths or prior project history through public issues or pull requests.

Use the declared runtime in an isolated environment. From the reviewed source root, with the package installed noneditably, run:

```sh
python -m unittest discover -s tests -v
```

The suite includes components loaded directly from this source tree. It does not by itself verify the installed application. Check the installed package location and exact source identity separately, and exercise the installed analyst workflow. Reinstall after source changes; a noneditable installation does not automatically reflect edits. Use neutral synthetic fixtures in committed tests. Real-template calculations require separately obtained original template bytes and a retained receipt; do not substitute saved-cache agreement for fresh Excel verification.

A change should include the reason, actual behaviour, relevant validation and remaining limitations. Update the README or reference documentation when the public contract changes. Preserve full precision, comparison tolerance and spreadsheet error classes. Never change a tolerance simply to obtain a pass.

The optional synthetic browser suite is `tests/presets.js`. It requires Node.js, Playwright available to Node, and a local Chrome executable selected with `CHROME_EXECUTABLE`. Run `node tests/presets.js`; use `QA_OUTPUT` to choose a private results directory. It uses neutral API fixtures and a separate browser profile, preserves the browser sandbox, and does not calculate or verify a real workbook.

Export changes need tests for intended content and excluded private fields, plus inspection of actual PDF/PNG files. Interface changes need real browser checks, including unsaved edits and delayed requests. Packaging changes need clean installation, exact resource inventory, dependency notices and platform-specific testing.

Before any release, maintainers review the exact source and generated package contents, asset rights and history. Unknown or changed payloads require renewed review. Code review and a successful build are not publication approval. See SECURITY.md for reporting restrictions and the readiness documentation for outstanding acceptance work.
