# Read, check and share a scenario briefing

Start with the policy PDF. Its reading guide explains the question, starting workbook, comparison case and limits before the charts. Both report styles include the same assumptions and shared explanations. In Excel, start with **Read me first**, then open **Results** or the input tables.

This is a conditional comparison of selected debt indicators. It helps analysts discuss policy choices; it is not a complete DSA, an official debt-distress rating or an institutional endorsement. Assumed investment benefits are inputs, not returns estimated by this tool. Check what the baseline already includes, the sources and timing of changes, and a smaller or delayed benefit. Review financing availability as well as its assumed price and maturity.

## Which file should I use?

| Purpose | File |
|---|---|
| Read findings and reasoning | Policy PDF; Standard PDF for familiar framework charts |
| Reuse or inspect numbers | Excel workbook or CSV tables |
| Place a figure on a slide or document | PNG |
| Resize or edit vector artwork | SVG in compatible software |
| Inspect the complete exported calculation record | Data-and-assumptions JSON |
| Check whether files changed after export | Manifest, compared against a trusted original |
| Reopen assumptions in the app | Use the separate scenario-file download/import in step 3 |

A briefing packet is not an importable scenario file or a full workspace backup. Keep the original workbook and a separate private workspace backup when continuing the analysis.

## What do the checks establish?

The workbook fingerprint ties the analysis to an exact source file. Layout checks establish support for the expected template geometry. Checks against selected values already saved in the workbook are limited consistency checks. A fresh Excel comparison would require recalculating the same changed case in Microsoft Excel and comparing its outputs. Do not equate those different checks or infer that any of them establishes the realism of an assumption. Read the recorded status and warnings for each case.

**SHA-256 is the name of the file-fingerprint method.** It produces a long code from file contents. Renaming the file does not change that code; editing or resaving it can. The short chart reference is convenient for discussion; exact matching requires the full fingerprint. It is not a password, quality score, proof of authorship or guarantee that a forecast is correct. The manifest separately fingerprints the exported files; it cannot authenticate itself or the sender.

The Excel reader sheet and packet read-me define the technical table columns. CSV and JSON field names remain stable for reuse. Original workbooks and private journals are excluded, but shared assumptions and explanations can still be confidential. Review the actual packet before sending.

## How this fits the guidance

The [2018 IMF/WB Guidance Note, paragraphs 73–74](https://www.imf.org/-/media/files/publications/pp/2017/pp122617guidance-note-on-lic-dsf.pdf#page=36) distinguishes customized risk tests from illustrative policy and financing scenarios. This app supports bounded exploration; it does not implement the full stress-test suite or assign ratings.

The [2024 Supplement, paragraphs 4–6](https://www.imf.org/-/media/files/publications/pp/2024/english/ppea2024039.pdf#page=7) discusses these issues in its climate section: baseline coverage, sourced assumptions, alternative policy scenarios and financing realism. Applying those principles to a general scenario tool is our interpretation. Those considerations motivate the contextual prompts. Applying them does not constitute IMF or World Bank approval of this software or of an analyst's plan.


### Exact passages

These are printed page numbers. The PDF links account for the cover page and open at the relevant location.

- [Illustrative financing scenarios](https://www.imf.org/-/media/files/publications/pp/2017/pp122617guidance-note-on-lic-dsf.pdf#page=38): 2018 Guidance Note, printed p. 37, paragraph 74: illustrations of financing needs and risks are distinct from risk-rating exercises.
- [Customized risk scenarios](https://www.imf.org/-/media/files/publications/pp/2017/pp122617guidance-note-on-lic-dsf.pdf#page=36): 2018 Guidance Note, printed p. 35, paragraph 73: customized scenarios can also be used in formal risk analysis, a separate use.
- [Baseline coverage and sources](https://www.imf.org/-/media/files/publications/pp/2024/english/ppea2024039.pdf#page=7): 2024 Supplement, climate section, printed p. 6, paragraph 4: explain baseline coverage, policy effects, sources and realism adjustments.
- [Alternative policy assumptions](https://www.imf.org/-/media/files/publications/pp/2024/english/ppea2024039.pdf#page=8): 2024 Supplement, climate section, printed pp. 7–8, paragraph 5: alternative policy scenarios, externally informed assumptions and realistic financing.
- [Climate stress testing](https://www.imf.org/-/media/files/publications/pp/2024/english/ppea2024039.pdf#page=9): 2024 Supplement, climate section, printed p. 8, paragraph 6: natural-disaster and customized stress tests have a separate role.
