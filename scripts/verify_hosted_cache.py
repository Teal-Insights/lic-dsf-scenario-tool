"""Source-bound startup cache and real hosted export acceptance; no browser or Linux claim."""
import argparse, hashlib, io, json, os, resource, sys, time, zipfile
from pathlib import Path
root = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('workbook', type=Path)
p.add_argument('accepted_packet', type=Path)
p.add_argument('--output-dir', type=Path, required=True)
a = p.parse_args()
os.environ['DSF_TEST_WORKBOOK'] = str(a.workbook.resolve())
sys.path.insert(0, str(root / 'tests'))
from test_hosted import Client
from lic_dsf.hosted import HostedApplication, OFFICIAL_EXAMPLE_SHA
out = a.output_dir.resolve(); out.mkdir(parents=True, exist_ok=False)
def fingerprints():
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc', '.pyo'}}
source = fingerprints()
fields = ['workbook_sha256', 'contract_version', 'first_projection_year', 'input_years', 'scenario', 'scenario_hash', 'points', 'thresholds', 'evidence', 'warnings']
with zipfile.ZipFile(a.accepted_packet) as z:
    accepted = {r['share_label']: r for r in json.loads(z.read('data-and-assumptions.json'))['runs']}
receipt = {'passed': False, 'platform': sys.platform, 'fresh_excel': False, 'browser': False,
           'source_files': source, 'reference_packet_sha256': hashlib.sha256(a.accepted_packet.read_bytes()).hexdigest(), 'cases': []}
started = time.monotonic()
app = HostedApplication(out / 'runtime', a.workbook, 'https://demo.example', prepare_teaching=True, workshop_test=True)
receipt['startup_seconds'] = time.monotonic() - started
(out / 'raw-prepared-results.json').write_text(json.dumps({'identity': json.loads(app.prepared_cache._identity), 'results': [json.loads(x) for x in app.prepared_cache._results.values()]}, indent=2))
from lic_dsf.hosted_cache import REUSE_WARNING
def original_field(result, field):
    value = result[field]
    if field == 'evidence':
        assert value['execution']['fresh_calculation_for_visit'] is False
        assert value['execution']['mode'] == 'prepared_teaching_result_reused'
        return {k:v for k,v in value.items() if k != 'execution'}
    if field == 'warnings':
        assert REUSE_WARNING in value
        return [x for x in value if x != REUSE_WARNING]
    return value
try:
    client, stranger = Client(app).enter(), Client(app).enter()
    boot = client.call('/api/boot')[1]
    assert boot['example_available'] and not boot['example_requires_download']
    assert client.call('/api/example', {})[0] == 200
    context = client.call('/api/workbook?sha=' + OFFICIAL_EXAMPLE_SHA)[1]
    cases = context['builtin_investment_cases']; assert len(cases) == 3
    ids = []
    for case in cases:
        pack = case['scenario_file']; started = time.monotonic()
        code, saved, _ = client.call('/api/save', {'workbook_sha': OFFICIAL_EXAMPLE_SHA,
            'name': pack['share_label'], 'share_label': pack['share_label'],
            'definition': pack['definition'], 'shared_rationale': pack['shared_rationale']})
        assert code == 200, saved
        ids.append(saved['id'])
        assert stranger.call('/api/scenario?id=' + saved['id'])[0] == 400
        code, job, _ = client.call('/api/calculate', {'scenario_id': saved['id']})
        assert code == 202, job
        deadline = time.monotonic() + 195
        while time.monotonic() < deadline:
            status = client.call('/api/job?id=' + job['job_id'])[1]
            if status['status'] != 'running': break
            time.sleep(1)
        assert status['status'] == 'complete', status
        result = client.call('/api/scenario?id=' + saved['id'])[1]['run']['result']
        expected = accepted[pack['share_label']]['result']
        for field in fields: assert original_field(result, field) == expected[field], (case['id'], field)
        receipt['cases'].append({'label': pack['share_label'], 'points': len(result['points']),
            'exact_fields': fields, 'seconds': time.monotonic() - started})
        print('PASS', pack['share_label'], flush=True)
    context = client.call('/api/workbook?sha=' + OFFICIAL_EXAMPLE_SHA)[1]
    assert len(context['scenarios']) == 3
    # Reload cannot replace saved cases, and sharing the immutable catalog cannot leak them.
    assert client.call('/api/example', {})[0] == 200
    assert len(client.call('/api/workbook?sha=' + OFFICIAL_EXAMPLE_SHA)[1]['scenarios']) == 3
    assert stranger.call('/api/example', {})[0] == 200
    assert stranger.call('/api/workbook?sha=' + OFFICIAL_EXAMPLE_SHA)[1]['scenarios'] == []
    data = {'scenario_ids': ids, 'comparator_id': ids[0], 'workbook_sha': OFFICIAL_EXAMPLE_SHA,
            'expected_chart_context_revision': context['chart_context']['revision']}
    code, comparison, _ = client.call('/api/compare', data); assert code == 200, comparison
    assert comparison['comparator_id'] == ids[0]
    for run in comparison['runs']:
        assert run['shared_rationale'] == accepted[run['share_label']]['shared_rationale']
    for view in ('standard', 'briefing'):
        code, body, _ = client.call('/api/export', dict(data, format='svg', view=view, metric='public_pv_gdp'))
        assert code == 200 and b'<svg' in body, (code, body)
        (out / (view + '.svg')).write_bytes(body)
    code, body, _ = client.call('/api/export', dict(data, format='zip')); assert code == 200, body
    (out / 'briefing.zip').write_bytes(body)
    with zipfile.ZipFile(io.BytesIO(body)) as z:
        manifest = json.loads(z.read('manifest.json'))
        for name, item in manifest['files'].items():
            value = z.read(name)
            assert len(value) == item['bytes'] and hashlib.sha256(value).hexdigest() == item['sha256']
        exported = json.loads(z.read('data-and-assumptions.json'))
        for run in exported['runs']:
            expected = accepted[run['share_label']]
            for field in fields: assert original_field(run['result'], field) == expected['result'][field]
            assert run['shared_rationale'] == expected['shared_rationale']
        assert len(z.namelist()) == 35
        receipt['packet_files'] = len(z.namelist()); receipt['packet_hashes'] = len(manifest['files'])
    assert client.call('/api/delete', {})[0] == 200
    assert client.call('/api/boot')[0] == 401
    assert fingerprints() == source, 'Source changed during verification'
    receipt.update(passed=True, source_unchanged=True, child_peak_rss_bytes=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
finally:
    app.close()
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2))
print(json.dumps({k:v for k,v in receipt.items() if k != 'source_files'}, indent=2))
