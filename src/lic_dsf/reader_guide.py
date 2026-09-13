"""Plain-language orientation shared by briefing reports and tabular exports."""

def reader_sections():
    return [
        ('About this early-stage tool',
         'This briefing was prepared with an experimental release of the LIC-DSF Scenario Analysis Tool. '
         'We are developing the software iteratively and welcome stakeholder feedback and co-design. '
         'Send non-confidential feedback to lte@tealinsights.com. The recorded verification limits apply to these results.'),
        ('What this analysis answers',
         'How would the reported debt indicators change under the alternative assumptions supplied by the analyst? '
         'These are conditional scenarios, not estimated investment returns, a complete DSA or an official debt-distress risk rating or IMF/World Bank endorsement.'),
        ('Start with the policy question',
         'Read the policy report, then the shared explanations. Compare the benefits, costs and financing assumptions together. '
         'Check what is already included in the workbook baseline so a policy effect is not counted twice. '
         'An illustrative example is a teaching case, not a forecast or recommendation.'),
        ('Read the comparison correctly',
         'The comparison case is the saved scenario against which differences are measured. The workbook reference baseline stays visible separately. '
         'For a programme comparison, use a no-programme case with consistent other assumptions and financing treatment. '
         'A difference from the reference baseline is not, by itself, a programme effect.'),
        ('Read the numbers and limits',
         'PV means present value; PPG means public and publicly guaranteed debt. A percentage point (pp) is a change in a ratio: 40% to 39% is a fall of 1 percentage point. '
         'Results cover selected years only; gaps between years do not establish a peak or first threshold crossing. '
         'A lower debt indicator alone does not establish a better policy or a change in the official risk rating.'),
        ('What has been checked',
         'The files record the calculation and check results for the selected cases. Matching values already saved in a workbook '
         'is a limited consistency check. It is different from recalculating that same case in Microsoft Excel and comparing the results. '
         'Read the evidence status; a file reference never verifies the economic assumptions.'),
        ('Why the workbook reference matters',
         'It lets colleagues check whether they used the same exact workbook file. A file fingerprint is a long code calculated from '
         'the file contents using SHA-256. Renaming a file does not change its fingerprint; editing or resaving it can. '
         'The short code on charts is a convenient reference; use the full fingerprint for exact matching. '
         'It is not a password, a quality score or proof that the analysis is correct.'),
        ('Where to find the detail',
         'The Results table contains indicator values and differences. Macro assumptions and Financing contain the inputs; '
         'Shared explanations records the analyst’s reasoning. Evidence and the JSON file retain technical calculation records. '
         'Source-cell references identify the sheet and cell used, so an analyst can trace a number back to the supported workbook.'),
        ('Before sending the packet',
         'Check the labels, assumptions, explanations and intended audience. The original workbook and private journal are excluded, '
         'but the shared analysis can still be confidential. The manifest lists a fingerprint for each exported file so a colleague '
         'can detect whether it changed after export. It does not certify correctness or identify who sent it.'),
    ]


def technical_glossary():
    return [
        ('workbook_sha256', 'Full fingerprint of the original workbook; use it to match the exact source file.'),
        ('scenario / comparator', 'The case shown and the comparison case used to calculate differences.'),
        ('reference_baseline / as_supplied_customized', 'The workbook baseline and its supplied customized case, before this saved scenario’s changes.'),
        ('difference_pp', 'Scenario value minus comparison-case value, in percentage points of the stated ratio. A negative difference is a lower ratio, not automatically a better policy.'),
        ('threshold', 'The applicable framework threshold or benchmark where supplied; it is not a stand-alone risk rating.'),
        ('baseline_source_cell / customized_source_cell', 'Sheet and cell locations used to trace the reported values.'),
        ('input_row / projection_year / adjustment', 'The template input row, year and change entered, in the listed units; zero means no adjustment.'),
        ('result_sha256 / scenario_sha256', 'Fingerprints of the saved result and numerical assumptions for technical comparison; not quality scores.'),
        ('interest_rate_percent / grace_years / maturity_years', 'Scenario financing levels. Blank inherited values mean use workbook treatment; they do not mean zero interest or a zero-year loan.'),
        ('revision', 'The saved version of a scenario, including its shared text.'),
        ('contract_version / engine_identity_json', 'The calculation contract and software/dependency identities used for reproducibility.'),
        ('evidence_json / warnings_json', 'Machine-readable check outcomes and warnings. These do not add verification beyond the stated checks.'),
        ('manifest.json', 'Exported filenames, sizes and fingerprints used to detect later file changes.'),
    ]


def financing_comparison_note(terms):
    if len(terms) < 2:
        return 'Only one case is selected. Select another calculated case to compare alternative assumptions.'
    if all(value == terms[0] for value in terms[1:]):
        return 'The selected cases use the same financing-term treatment. This comparison does not test alternative borrowing terms. Review the macro paths to see what changes between cases.'
    return 'Financing-term treatment differs between the selected cases. Review the Financing table and shared explanations alongside the macro paths; check whether macro paths also differ before attributing a result to borrowing terms.'


def guidance_references():
    return [
        ('Illustrative financing scenarios', '2018 Guidance Note, printed p. 37, paragraph 74: illustrations of financing needs and risks are distinct from risk-rating exercises.', 'https://www.imf.org/-/media/files/publications/pp/2017/pp122617guidance-note-on-lic-dsf.pdf#page=38'),
        ('Customized risk scenarios', '2018 Guidance Note, printed p. 35, paragraph 73: customized scenarios can also be used in formal risk analysis, a separate use.', 'https://www.imf.org/-/media/files/publications/pp/2017/pp122617guidance-note-on-lic-dsf.pdf#page=36'),
        ('Baseline coverage and sources', '2024 Supplement, climate section, printed p. 6, paragraph 4: explain baseline coverage, policy effects, sources and realism adjustments.', 'https://www.imf.org/-/media/files/publications/pp/2024/english/ppea2024039.pdf#page=7'),
        ('Alternative policy assumptions', '2024 Supplement, climate section, printed pp. 7–8, paragraph 5: alternative policy scenarios, externally informed assumptions and realistic financing.', 'https://www.imf.org/-/media/files/publications/pp/2024/english/ppea2024039.pdf#page=8'),
        ('Climate stress testing', '2024 Supplement, climate section, printed p. 8, paragraph 6: natural-disaster and customized stress tests have a separate role.', 'https://www.imf.org/-/media/files/publications/pp/2024/english/ppea2024039.pdf#page=9'),
    ]


def comparison_orientation(summary):
    official = summary['provenance']['kind'] == 'official_illustrative_template'
    source = ('Official World Bank LIC-DSF template, IDA21 file version 08-12-2025. ' + summary['provenance']['disclosure']) if official else 'Analyst-supplied workbook in the supported LIC-DSF template format.'
    return [
        ('This comparison', summary['chart_context']['label'] or 'Selected scenario comparison'),
        ('Comparison case', summary['comparator']),
        ('Starting source', source + ' The alternative scenarios use supplied assumptions and are calculated by this tool; they are not forecasts supplied by the World Bank.'),
        ('Recorded check status', '; '.join(item['scenario'] + ': ' + item['status'] for item in summary['evidence'])),
        ('What varies in this comparison', financing_comparison_note([a['financing_terms'] for a in summary['assumptions']])),
    ]
