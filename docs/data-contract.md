# Saved scenarios and comparison JSON

The JSON Schema files in `schemas/` describe the portable scenario definition, historical v1 comparison and current v2 shareable comparison. They use JSON Schema draft 2020-12. Resolve the comparison schema's relative reference to `scenario-v1.schema.json` from the same directory; validation needs no network schema fetch.

These schemas document shape. They are not an import feature, privacy filter, numerical verification receipt or publication approval. Reject non-standard JSON values such as NaN and Infinity before validation. Application checks add finite-number and relational constraints that JSON Schema does not express here.

## Scenario definitions

`delta_paths` contains exactly 13 workbook row identifiers, each with 21 explicit numeric entries. The matching `input_years` array in a run supplies the year labels; offset zero is the first projection year. The row identifiers and units are described in the methodology. A numeric zero is an explicit adjustment; a blank editor field is invalid.

`terms: null` preserves supplied financing values and formulas. An object replaces all three financing terms. Interest rate is a decimal; grace and maturity are whole years. In addition to the schema, the application requires maturity to exceed grace. A scenario definition is not meaningful without its workbook identity and year mapping.

## Comparison records

`format` is `lic-dsf-comparison-v2` for new exports. A record carries one workbook SHA-256, a selected comparator ID, an explicit `chart_context` and saved runs. Each run includes its intentionally shareable label, saved revision, scenario definition, numerical results, runtime identity and evidence. Private names and journal text are excluded by the application's explicit export selection.

Every result has 36 observations: six supported indicators at projection offsets 0, 2, 5, 10, 15 and 20. Each observation retains reference baseline, as-supplied customized and selected scenario values, along with source cells and units. Missing/error observations must not be converted to zero. A consumer must check that metric/year pairs are unique and complete, years and units agree across runs, all workbook identities match the enclosing record, the comparator belongs to the runs and reference-baseline channels agree.

Chart rendering accepts one to four distinct shared labels and rejects path-like labels. JSON may contain more runs; schema validity alone does not establish that a chart can render the comparison. The current application exports only calculations labelled `computed_unverified` with matching saved-cache checks. That remains distinct from live Excel acceptance.

Optional `workbook_provenance` identifies the exact official illustrative example when its bytes match the recorded source hash. An edited workbook is user supplied; its illustrative status is not inferred from a filename or country label. Retain all supplied disclosures when transforming or sharing a record.

## Identities and integrity

Workbook SHA-256 identifies original bytes. Scenario hashes use UTF-8 JSON with sorted keys, compact separators, non-ASCII characters preserved and nonfinite values refused. Runtime identity includes the package's Python source, evaluator revision, relevant dependency versions and platform information. Changed identities invalidate current results rather than silently reusing them.

A run's exported `result_hash` identifies the original complete saved result, before export-field selection. It is not the hash of the shortened exported `result` object or the downloaded JSON file. Retain the original workspace for full audit/recovery. File hashes are identifiers, not anonymisation or evidence of economic correctness.

## Shared chart context and compatibility

`chart_context` contains exactly `workbook_sha256`, `label` and `revision`. Its full source hash must equal the enclosing comparison and every run. A never-set context is null with revision zero; clearing an existing label retains a positive revision. Labels are deliberately outward text, not uploaded filenames, internal names or journal excerpts. Runtime validation checks canonical text, supported fiscal-year notation, source equality and revision consistency; schema validation alone does not establish all of these relations.

The context revision is independent of numerical scenario revisions. Editing a saved label changes neither the saved calculation nor its result hash. HTTP compare/export requests supply the full workbook hash and expected context revision, so another tab’s changed label cannot silently enter an export. The label and numerical runs are read from one storage snapshot. Downloaded JSON is a snapshot, not a live link to future label edits.

The renderer still reads old `lic-dsf-comparison-v1` records without a label and displays their workbook identifier. The historical v1 schema remains unchanged; strict downstream validators must select the v2 schema for new files. A supplied malformed context or unknown comparison version is rejected. The numerical `ida21-local-v1` contract and scenario-v1 definition remain unchanged.

Workspace schema 1 migrates additively to schema 2 for the per-workbook context table. Existing scenario, result and journal records are not rewritten. Unsupported versions or malformed schemas are rejected before mutation. Preserve a stopped workspace backup before upgrading; the older application cannot open schema 2. There is still no comparison-JSON re-import interface.
