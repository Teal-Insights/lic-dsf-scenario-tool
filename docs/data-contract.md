# Scenario files, saved definitions and comparison JSON

The JSON Schema files in `schemas/` describe the [scenario-file envelope](../schemas/scenario-file-v1.schema.json), [numerical definition](../schemas/scenario-v1.schema.json), historical v1/v2 comparisons and [current v3 comparison](../schemas/comparison-v3.schema.json). They use JSON Schema draft 2020-12. Resolve relative references to `scenario-v1.schema.json` from the same directory; validation needs no network schema fetch.

These schemas document shape. The browser imports only the scenario-file envelope described below. Schema validation alone is not a privacy filter, numerical verification receipt or publication approval. Reject non-standard JSON values such as NaN and Infinity before validation. Application checks add finite-number and relational constraints that JSON Schema does not express here.

## Scenario definitions

`delta_paths` contains exactly 13 workbook row identifiers, each with 21 explicit numeric entries. The matching `input_years` array in a run supplies the year labels; offset zero is the first projection year. The [input reference](workbooks-inputs-outputs.md#enter-annual-adjustments) maps every row identifier to its name and units. A numeric zero is an explicit adjustment; a blank editor field is invalid.

`terms: null` preserves supplied financing values and formulas. An object replaces all three financing terms. Interest rate is a decimal; grace and maturity are whole years. In addition to the schema, the application requires maturity to exceed grace. A scenario definition is not meaningful without its workbook identity and year mapping.

## Scenario files

The envelope has exactly these six required fields:

| Field | Meaning |
| --- | --- |
| `format` | The literal `lic-dsf-scenario-v1` |
| `workbook_sha256` | Full lowercase 64-character SHA-256 of the exact original workbook |
| `input_years` | All 21 projection years in order, exactly matching the loaded workbook |
| `definition` | Complete `delta_paths` and `terms`, using the numerical definition above |
| `share_label` | Deliberately shared chart label, 1–40 characters |
| `shared_rationale` | Object mapping supported row identifiers or `financing` to shared explanations, at most 1,500 characters each; `{}` is valid |

The maximum file size is 131,072 bytes. All 13 paths must contain finite numbers for every year. Unknown fields are rejected at the envelope, definition, path-key and financing levels; shared-explanation keys must be supported inputs. Labels cannot be blank, path/link-like or the reserved “Reference baseline”. Explanations allow line breaks but not tabs, carriage returns or hidden control characters. Normal saved-text validation still applies when the draft is saved, including distinct chart labels within the workbook.

The [scenario-file schema](../schemas/scenario-file-v1.schema.json) describes structural and length limits. Application checks additionally enforce exact loaded-workbook/year equality, finite numbers, maturity greater than grace, text restrictions and saved-label uniqueness. A consumer must enforce these relations as well as the byte limit; schema validity alone does not prove that a file can be saved.

Download rereads the current saved scenario revision and refuses a stale revision from another tab. It selects only the six fields above, excluding the workbook, internal name, private journal, chart heading, calculation results and evidence. Import opens a new unsaved draft, using `share_label` as both initial workspace name and chart label. It cannot overwrite an existing case or import a verified result. Review, save and calculate it through the normal workflow.

Only exact-workbook, single-case exchange is supported. There is no cross-workbook/year remapping, upstream-model translation, bulk case-set import or comparison-JSON import. See the [exchange steps](exchange-recovery.md#share-or-reuse-one-scenario).

## Comparison records

`format` is `lic-dsf-comparison-v3` for new exports. A record carries one workbook SHA-256, a selected comparator ID, an explicit `chart_context` and saved runs. Each run includes its intentionally shareable label, saved revision, scenario definition, numerical results, runtime identity and evidence. Private names and journal text are excluded by the application's explicit export selection.

Every result has 36 observations: six supported indicators at projection offsets 0, 2, 5, 10, 15 and 20. Each observation retains reference baseline, as-supplied customized and selected scenario values, along with source cells and units. Missing/error observations must not be converted to zero. A consumer must check that metric/year pairs are unique and complete, years and units agree across runs, all workbook identities match the enclosing record, the comparator belongs to the runs and reference-baseline channels agree.

Chart rendering accepts one to four distinct shared labels and rejects path-like labels. JSON may contain more runs; schema validity alone does not establish that a chart can render the comparison. The current application exports only calculations labelled `computed_unverified` with matching saved-cache checks. That remains distinct from live Excel acceptance.

Optional `workbook_provenance` identifies the exact official illustrative example when its bytes match the recorded source hash. An edited workbook is user supplied; its illustrative status is not inferred from a filename or country label. Retain all supplied disclosures when transforming or sharing a record.

## Identities and integrity

Workbook SHA-256 identifies original bytes. Scenario hashes use UTF-8 JSON with sorted keys, compact separators, non-ASCII characters preserved and nonfinite values refused. Runtime identity includes the package's Python source, evaluator revision, relevant dependency versions and platform information. Changed identities invalidate current results rather than silently reusing them.

A run's exported `result_hash` identifies the original complete saved result, before export-field selection. It is not the hash of the shortened exported `result` object or the downloaded JSON file. Retain the original workspace for full audit/recovery. File hashes are identifiers, not anonymisation or evidence of economic correctness.

## Shared chart context and compatibility

`chart_context` contains exactly `workbook_sha256`, `label` and `revision`. Its full source hash must equal the enclosing comparison and every run. A never-set context is null with revision zero; clearing an existing label retains a positive revision. Labels are deliberately outward text, not uploaded filenames, internal names or journal excerpts. Runtime validation checks canonical text, supported fiscal-year notation, source equality and revision consistency; schema validation alone does not establish all of these relations.

Legend labels and the heading can be applied together through one atomic operation (`/api/chart-text`), which validates every value before writing, checks each case's expected revision and the context revision in one transaction, refuses a final label set with duplicates or the reserved “Reference baseline”, and rolls back completely on any refusal. The context revision is independent of numerical scenario revisions. Editing a saved label changes neither the saved calculation nor its result hash. HTTP compare/export requests supply the full workbook hash and expected context revision, so another tab’s changed label cannot silently enter an export. The label and numerical runs are read from one storage snapshot. Downloaded JSON is a snapshot, not a live link to future label edits.

The renderer still reads old `lic-dsf-comparison-v1` records without a label and displays their workbook identifier. The historical v1 schema remains unchanged; strict downstream validators must select the v3 schema for new files. A supplied malformed context or unknown comparison version is rejected. The numerical `ida21-local-v1` contract and scenario-v1 definition remain unchanged.

Workspace schemas 1 and 2 migrate additively to schema 3: the context table is retained or created, and a shared-explanation table is added. Existing scenario, result and journal records are not rewritten. Unsupported versions or malformed schemas are rejected before mutation. Preserve a stopped workspace backup before upgrading; older application versions cannot open schema 3. There is still no comparison-JSON re-import interface.

## Shared explanations in version 3

Each run has `shared_rationale`, a map of supported input row identifiers or `financing` to intentionally shared text (at most 1,500 characters per entry). These are scenario-revision metadata, separate from numerical `scenario` definitions and private journals. Unicode is normalized to NFC, outer whitespace removed, empty entries omitted, and hidden controls other than line breaks refused. Text is rendered literally. A PDF with unsupported font characters is refused with an explanation; JSON preserves valid Unicode.

During workspace migration every historical scenario revision gets an empty map. No private journal is promoted to a shared note. Shared notes have their own stored integrity hash; missing or corrupted metadata blocks loading. Scenario saves record notes atomically with the revision. Omission by an older API caller preserves existing notes; an explicit empty map clears them on the new revision. A revision that changes the numerical definition requires calculation before comparison/export. A revision that changes only the name, the legend label or the shared explanations keeps the calculation of the revision it was saved from, because the numerical `definition_hash` is unchanged; a restored definition after an intervening numerical change still needs its own calculation. The exported `revision` is the current saved revision and `result_hash` identifies the unchanged saved result. Historical numerical results and their hashes are not rewritten.

The PDF annex identifies adjusted drivers without notes as **No explanation provided**. PNGs contain charts only. Comparison JSON remains a results export. Only the separate `lic-dsf-scenario-v1` envelope can be imported as editable assumptions.

## Read a numerical definition

For the tutorial's lower-growth case, key `"20"` contains `[-1, -1, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]`. All 12 other required row keys contain 21 zeros. `terms` is `null`. The run's `input_years` labels these entries 2024 through 2044 for the exact official example. This excerpt illustrates fields; it is not a complete importable file.

An explicit financing override has the form `{"rate": 0.04, "grace_years": 5, "maturity_years": 20}`. The browser displays its rate as 4 percent. Preserve that unit conversion when reading JSON; storing 4 in the rate field means 400 percent.

Consumers should preserve the original file and validate using the declared comparison version and the accompanying [scenario schema](../schemas/scenario-v1.schema.json). Use `points` and their explicit year/unit/source cells rather than relying on chart rounding or fixed array positions. Check application-level relations described above after shape validation.

For sharing and continued editing, see [exchange and recovery](exchange-recovery.md). [Documentation index](README.md).
