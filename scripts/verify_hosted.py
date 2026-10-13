import io,json,os,sys,time,zipfile,hashlib,resource,argparse
from pathlib import Path
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description='Run source-bound hosted API calculation, quota and packet checks; no browser or Linux claim.')
parser.add_argument('workbook',type=Path);parser.add_argument('--output-dir',type=Path,required=True)
args=parser.parse_args()
os.environ['DSF_TEST_WORKBOOK']=str(args.workbook.resolve())
sys.path.insert(0,str(root/'tests'))
sys.path.insert(0,str(root/'scripts'))
from test_hosted import Client, BOOK
from lic_dsf.hosted import HostedApplication, OFFICIAL_EXAMPLE_SHA
from verify_official_example import compare, EXPECTED_FIELDS
out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=False)
def fingerprints():
 return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'}}
source_before=fingerprints()
app=HostedApplication(out/'runtime',BOOK,'https://demo.example')
a,b=Client(app).enter(),Client(app).enter()
assert a.call('/api/example',{})[0]==200
fixture=json.loads((root/'tests/fixtures/official-example-regression.json').read_text())
receipt={'platform':sys.platform,'fresh_excel':False,'cases':[],'source_files':source_before}
ids=[]
try:
 for item in fixture['cases']:
  started=time.monotonic()
  code,saved,_=a.call('/api/save',{'workbook_sha':OFFICIAL_EXAMPLE_SHA,'name':item['case'],'share_label':item['case'],'definition':item['expected']['scenario']})
  assert code==200,(code,saved)
  ids.append(saved['id'])
  code,job,_=a.call('/api/calculate',{'scenario_id':saved['id']});assert code==202,job
  assert b.call('/api/job?id='+job['job_id'])[1]['status']=='interrupted'
  assert a.call('/api/calculate',{'scenario_id':saved['id']})[0]==400
  if len(ids)>1:
   context=a.call('/api/workbook?sha='+OFFICIAL_EXAMPLE_SHA)[1]['chart_context']
   busy_data={'scenario_ids':[ids[0]],'comparator_id':ids[0],'workbook_sha':OFFICIAL_EXAMPLE_SHA,'expected_chart_context_revision':context['revision'],'format':'zip'}
   code,message,_=a.call('/api/export',busy_data)
   assert code==400 and 'retry shortly' in message['error'],message
   assert next(ws for ws in app.sessions.values() if ws.token==a.token).exports==0
   receipt['busy_export_during_real_calculation']=True
  while True:
   status=a.call('/api/job?id='+job['job_id'])[1]
   if status['status']!='running':break
   time.sleep(1)
  assert status['status']=='complete',status
  result=a.call('/api/scenario?id='+saved['id'])[1]['run']['result']
  leaves=compare(item['expected'],{key:result[key] for key in EXPECTED_FIELDS})
  receipt['cases'].append({'name':item['case'],'seconds':time.monotonic()-started,'checked_leaves':leaves,'evidence':result['evidence']})
  print('PASS',item['case'],receipt['cases'][-1]['seconds'],flush=True)
 context=a.call('/api/workbook?sha='+OFFICIAL_EXAMPLE_SHA)[1]['chart_context']
 data={'scenario_ids':ids,'comparator_id':ids[0],'workbook_sha':OFFICIAL_EXAMPLE_SHA,'expected_chart_context_revision':context['revision']}
 for route in ['/api/compare','/api/export']:
  assert b.call(route,data)[0]==400
 code,comparison,_=a.call('/api/compare',data);assert code==200,comparison
 (out/'comparison.json').write_text(json.dumps(comparison,indent=2))
 for view in ['standard','briefing']:
  code,body,_=a.call('/api/export',dict(data,format='svg',view=view,metric='ext_pv_gdp'))
  assert code==200 and b'<svg' in body,(code,body)
  (out/(view+'.svg')).write_bytes(body)
 # Fill the unchanged response budget with lightweight validated JSON exports.
 for _ in range(27):
  code,body,_=a.call('/api/export',dict(data,format='json'));assert code==200
 code,message,_=a.call('/api/export',dict(data,format='svg',view='standard',metric='ext_pv_gdp'))
 assert code==400 and 'reserved final slot' in message['error']
 started=time.monotonic()
 code,body,_=a.call('/api/export',dict(data,format='zip'))
 assert code==200,(code,body)
 (out/'briefing.zip').write_bytes(body)
 with zipfile.ZipFile(io.BytesIO(body)) as z:
  manifest=json.loads(z.read('manifest.json'))
  for name,item in manifest['files'].items():
   contents=z.read(name);assert len(contents)==item['bytes'] and hashlib.sha256(contents).hexdigest()==item['sha256']
  receipt['packet_hashes_verified']=len(manifest['files'])
  names=z.namelist();assert len([n for n in names if n.endswith('.pdf')])==2
  assert len([n for n in names if n.endswith('.svg')])==12
  assert len([n for n in names if n.endswith('.png')])==12
  assert len([n for n in names if n.endswith('.csv')])==5
 receipt['export']={'seconds':time.monotonic()-started,'bytes':len(body),'files':names}
 receipt['child_peak_rss_bytes']=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
 receipt['visitor_bytes']=sum(p.stat().st_size for p in app.visitors.rglob('*') if p.is_file())
 assert not list(app.visitors.rglob('*.log'))
 assert a.call('/api/export',dict(data,format='zip'))[0]==400
 receipt['reserved_packet_at_slot_30']=True
 assert fingerprints()==source_before,'Source changed during verification'
 receipt['source_unchanged']=True
 receipt['passed']=True
 print(json.dumps({k:v for k,v in receipt.items() if k!='source_files'},indent=2),flush=True)
finally:
 app.close()
 (out/'numerical-receipt.json').write_text(json.dumps(receipt,indent=2))
