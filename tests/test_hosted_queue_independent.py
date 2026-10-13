"""Actual WSGI+queue controls; synthetic comparison, no numerical/render claims."""
import copy,os,sys,tempfile,time,threading,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from lic_dsf.hosted import HostedApplication,OFFICIAL_EXAMPLE_SHA
from test_hosted import Client
BOOK=os.environ.get('DSF_TEST_WORKBOOK')

@unittest.skipUnless(BOOK, 'Supply the exact official workbook outside source.')
class QueueTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.now=0
  with patch('lic_dsf.hosted_cache.prepare',return_value=None):
   self.app=HostedApplication(self.tmp.name,BOOK,'https://demo.example',prepare_teaching=True,workshop_test=True,clock=lambda:self.now,sweep=False)
  self.share=patch('lic_dsf.app.shareable',side_effect=copy.deepcopy);self.share.start();self.clients=[]
 def tearDown(self):
  self.share.stop();self.app.close();self.tmp.cleanup()
 def client(self):
  c=Client(self.app).enter();ws=self.app.sessions[c.cookie.split('=',1)[1]]
  marker='Visitor'+str(len(self.clients))+'sentinel';record={'label':marker,'explanation':marker}
  ws.comparison=lambda data:copy.deepcopy(record)
  self.clients.append(c);return c,ws,record
 def query(self,fmt='json',key='request-1'):
  return {'scenario_ids':['synthetic-case'],'comparator_id':'synthetic-case','workbook_sha':OFFICIAL_EXAMPLE_SHA,
          'expected_chart_context_revision':0,'format':fmt,'request_key':key}
 def submit(self,c,fmt='json',key='request-1'):
  code,value,_=c.call('/api/export-jobs',self.query(fmt,key));self.assertEqual(code,202,value);return value['job_id']
 def state(self,c,j):return c.call('/api/export-status?id='+j)
 def wait(self,c,j,status='ready'):
  deadline=time.monotonic()+3
  while time.monotonic()<deadline:
   value=self.state(c,j)[1]
   if value.get('status')==status:return value
   time.sleep(.01)
  self.fail(value)
 def test_malformed_request_returns_400(self):
  c,ws,_=self.client()
  for value in [[],{},True]:
   code,body,_=c.call('/api/export-jobs',self.query(value))
   self.assertEqual(code,400,body)
  self.assertEqual(ws.exports,0)
 def test_rejected_overquota_preserves_ready_replay(self):
  c,ws,_=self.client();ws.exports=29
  ws._render_export=lambda *_:(b'final-packet','application/zip','packet.zip')
  j=self.submit(c,'zip');self.wait(c,j);self.assertEqual(ws.exports,30)
  self.assertEqual(c.call('/api/export-jobs',self.query('zip','extra'))[0],400)
  self.assertEqual(c.call('/api/export-result?id='+j)[0],200)
 def test_fifo_25_privacy_frozen_comparison_and_replay(self):
  allvisitors=[self.client() for _ in range(25)];order=[];jobs=[]
  self.assertTrue(self.app.compute.acquire(False))
  try:
   for i,(c,ws,record) in enumerate(allvisitors):
    original=ws.bounded_export
    def wrapped(comparison,data,*,count_response=True,index=i,base=original):
     order.append(index);return base(comparison,data,count_response=count_response)
    ws.bounded_export=wrapped
    j=self.submit(c,key='request-'+str(i));jobs.append(j)
    record['label']='CHANGED_AFTER_SUBMIT'
    self.assertEqual(c.call('/api/export-jobs',self.query(key='duplicate'))[0],400)
   self.assertEqual(len(self.app.export_queue.jobs),25)
  finally:self.app.compute.release()
  for i,((c,ws,_),j) in enumerate(zip(allvisitors,jobs)):
   self.wait(c,j);first=c.call('/api/export-result?id='+j);second=c.call('/api/export-result?id='+j)
   self.assertEqual(first[0],200);self.assertEqual(first[1],second[1]);self.assertEqual(ws.exports,1)
   text=first[1].decode();self.assertIn('Visitor'+str(i)+'sentinel',text);self.assertNotIn('CHANGED_AFTER_SUBMIT',text)
   other=allvisitors[(i+1)%25][0]
   for route in ['/api/export-status?id=','/api/export-result?id=']:self.assertEqual(other.call(route+j)[0],404)
   self.assertEqual(other.call('/api/export-cancel',{'job_id':j})[0],404)
  self.assertEqual(order,list(range(25)))
 def test_cancel_queued_and_background_expiry(self):
  c,ws,_=self.client();self.app.compute.acquire()
  try:
   j=self.submit(c);self.assertEqual(c.call('/api/export-cancel',{'job_id':j})[0],200)
   self.assertEqual(self.state(c,j)[1]['status'],'cancelled');self.assertEqual(ws.exports,0)
   j=self.submit(c,key='expiry');self.now=601
   deadline=time.monotonic()+2
   while time.monotonic()<deadline and self.app.export_queue.own(ws,j)['status']!='expired':time.sleep(.02)
   self.assertEqual(self.app.export_queue.own(ws,j)['status'],'expired');self.assertEqual(ws.exports,0)
  finally:self.app.compute.release()
 def test_cancel_at_both_request_limits_preserves_inputs_and_auth(self):
  from lic_dsf.illustrative import builtin_investment_cases,OFFICIAL_YEARS
  c,ws,_=self.client();other,_,_=self.client()
  definition=builtin_investment_cases(OFFICIAL_EXAMPLE_SHA,OFFICIAL_YEARS)[0]['scenario_file']['definition']
  ws.store.register_workbook(OFFICIAL_EXAMPLE_SHA,'Official illustrative example')
  saved=ws.store.save_scenario(OFFICIAL_EXAMPLE_SHA,'Saved synthetic inputs',definition,share_label='Retained inputs')
  before=ws.store.get_scenario(saved['id'])
  self.assertTrue(self.app.compute.acquire(False))
  try:
   j=self.submit(c)
   ws.requests=600;self.app.hits.clear();self.app.hits.extend([self.now]*self.app.max_hits)
   self.assertEqual(c.call('/api/export-status?id='+j)[0],429)
   self.assertEqual(c.call('/api/export-cancel',{'job_id':j},HTTP_ORIGIN='https://outside.example')[0],403)
   self.assertEqual(c.call('/api/export-cancel',{'job_id':j},HTTP_X_DSF_TOKEN='wrong-token')[0],403)
   self.assertEqual(c.call('/api/export-cancel',{'job_id':j},CONTENT_LENGTH='131073')[0],413)
   self.assertEqual(other.call('/api/export-cancel',{'job_id':j})[0],404)
   self.assertEqual(self.app.export_queue.own(ws,j)['status'],'queued')
   self.assertEqual(c.call('/api/export-cancel',{'job_id':j})[0],200)
   self.assertEqual(self.app.export_queue.own(ws,j)['status'],'cancelled')
   self.assertEqual(ws.exports,0);self.assertFalse(ws.closed)
   self.assertEqual(ws.store.get_scenario(saved['id']),before)
   self.assertEqual(len(self.app.hits),self.app.max_hits)
  finally:self.app.compute.release()
 def test_cancel_running_releases_permit_without_charge(self):
  c,ws,_=self.client();entered=threading.Event();released=threading.Event()
  class Child:
   dead=False
   def poll(self):return -9 if self.dead else None
   def kill(self):self.dead=True;released.set()
   def wait(self,timeout):self.assertion=timeout
  child=Child()
  def render(*_):
   ws.export_child=child;self.app.lock.release()
   try:entered.set();assert released.wait(3)
   finally:self.app.lock.acquire();ws.export_child=None
   return b'cancelled-body','image/svg+xml','chart.svg'
  ws._render_export=render
  j=self.submit(c,'svg');self.assertTrue(entered.wait(2))
  self.assertEqual(c.call('/api/export-cancel',{'job_id':j})[0],200)
  self.wait(c,j,'cancelled');deadline=time.monotonic()+2
  while time.monotonic()<deadline:
   if self.app.compute.acquire(False):self.app.compute.release();break
   time.sleep(.01)
  else:self.fail('permit not released')
  self.assertTrue(child.dead);self.assertEqual(ws.exports,0);self.assertEqual(c.call('/api/export-result?id='+j)[0],410)
 def test_ready_ttl_and_delete_cleanup(self):
  c,ws,_=self.client();j=self.submit(c);self.wait(c,j);self.assertEqual(ws.exports,1)
  self.now=61
  self.wait(c,j,'expired');self.assertEqual(c.call('/api/export-result?id='+j)[0],410)
  self.assertEqual(ws.exports,1)
  ws.requests=600
  self.assertEqual(c.call('/api/delete',{})[0],200);self.assertFalse(ws.directory.exists())
  self.assertFalse(self.app.export_queue.jobs)
 def test_failure_survival_and_final_zip_reservation(self):
  c,ws,_=self.client()
  def fail(*_):raise ValueError('synthetic renderer failure')
  ws._render_export=fail;j=self.submit(c,'svg');self.wait(c,j,'failed');self.assertEqual(ws.exports,0)
  ws.exports=28;j=self.submit(c,key='slot29');self.wait(c,j);self.assertEqual(ws.exports,29)
  self.assertEqual(c.call('/api/export-jobs',self.query('json','denied'))[0],400)
  ws._render_export=lambda *_:(b'packet','application/zip','packet.zip')
  j=self.submit(c,'zip','slot30');self.wait(c,j);self.assertEqual(ws.exports,30)
  self.assertEqual(c.call('/api/export-cancel',{'job_id':j})[0],200);self.assertEqual(ws.exports,30)

if __name__=='__main__':unittest.main(verbosity=2)
