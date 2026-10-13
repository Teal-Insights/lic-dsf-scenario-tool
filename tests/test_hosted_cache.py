"""Synthetic boundary tests, explicitly not numerical validation."""
import copy,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from lic_dsf.hosted_cache import PreparedCache,canonical_definitions,OFFICIAL_SHA256,OFFICIAL_YEARS,CONTRACT_VERSION,prepare
from lic_dsf.engine import digest
IDENTITY={'synthetic_boundary_test':True,'contract_version':CONTRACT_VERSION}

def fixture():
    results=[]
    for definition in canonical_definitions():
        value={'contract_version':CONTRACT_VERSION,'workbook_sha256':OFFICIAL_SHA256,
            'first_projection_year':2024,'input_years':list(OFFICIAL_YEARS),'engine_identity':IDENTITY,
            'scenario':definition,'scenario_hash':digest(definition),'points':[{'synthetic':True}]*36,
            'thresholds':{},'evidence':{'calculation':'computed_unverified'},'warnings':[],
            'created_utc':'synthetic'}
        value['run_hash']=digest(value);results.append(value)
    return results

def rehash(value):
    value.pop('run_hash',None);value['run_hash']=digest(value)

class BoundaryTests(unittest.TestCase):
    def test_trio_tamper_and_foreign_fields(self):
        for mode in ['missing','duplicate','bad_hash','visitor_name','contract','workbook','points','definition']:
            values=fixture()
            if mode=='missing':values.pop()
            elif mode=='duplicate':values[2]=copy.deepcopy(values[1])
            elif mode=='bad_hash':values[0]['run_hash']='a'*64
            elif mode=='visitor_name':values[0]['visitor_name']='Private sentinel';rehash(values[0])
            elif mode=='contract':values[0]['contract_version']='other';rehash(values[0])
            elif mode=='workbook':values[0]['workbook_sha256']='b'*64;rehash(values[0])
            elif mode=='points':values[0]['points'].pop();rehash(values[0])
            else:values[0]['scenario']['delta_paths']['20'][0]=.123;rehash(values[0])
            with self.subTest(mode=mode),self.assertRaises(ValueError):PreparedCache(values,IDENTITY)
    def test_identity_and_numeric_misses(self):
        cache=PreparedCache(fixture(),IDENTITY);definition=canonical_definitions()[0]
        with patch('lic_dsf.hosted_cache.engine_identity',return_value=IDENTITY):
            self.assertIsNone(cache.lookup('b'*64,definition))
            changed=copy.deepcopy(definition);changed['terms']['rate']+=.001
            self.assertIsNone(cache.lookup(OFFICIAL_SHA256,changed))
        with patch('lic_dsf.hosted_cache.engine_identity',return_value={'other':True}):
            self.assertIsNone(cache.lookup(OFFICIAL_SHA256,definition))
    def test_immutable_storage_fresh_copies_provenance(self):
        values=fixture();cache=PreparedCache(values,IDENTITY);definition=canonical_definitions()[0]
        with self.assertRaises(TypeError):cache._results['new']='bad'
        values[0]['scenario']['delta_paths']['20'][0]=99
        with patch('lic_dsf.hosted_cache.engine_identity',return_value=IDENTITY):
            first=cache.lookup(OFFICIAL_SHA256,definition)
            self.assertFalse(first['evidence']['execution']['fresh_calculation_for_visit'])
            first['scenario']['delta_paths']['20'][0]=88
            second=cache.lookup(OFFICIAL_SHA256,definition)
            self.assertEqual(second['scenario'],definition)
            raw=copy.deepcopy(second);stored=raw.pop('run_hash');self.assertEqual(stored,digest(raw))
    @unittest.skipUnless(os.environ.get('DSF_TEST_WORKBOOK'),'separately supplied official input needed')
    def test_prepare_child_failure_removes_scratch(self):
        class Failed:
            returncode=1
            def wait(self,**kw):pass
        with tempfile.TemporaryDirectory() as root,patch('lic_dsf.hosted_cache.engine_identity',return_value=IDENTITY),patch('lic_dsf.hosted_cache.subprocess.Popen',return_value=Failed()):
            with self.assertRaises(ValueError):prepare(os.environ['DSF_TEST_WORKBOOK'],root)
            self.assertEqual(list(Path(root).iterdir()),[])
    @unittest.skipUnless(os.environ.get('DSF_TEST_WORKBOOK'),'separately supplied official input needed')
    def test_constructor_failure_closes_lease(self):
        from lic_dsf.hosted import HostedApplication
        with tempfile.TemporaryDirectory() as root:
            with patch('lic_dsf.hosted_cache.prepare',side_effect=ValueError('synthetic failed prewarm')):
                with self.assertRaises(ValueError):HostedApplication(root,os.environ['DSF_TEST_WORKBOOK'],'https://demo.example',prepare_teaching=True,sweep=False)
            app=HostedApplication(root,os.environ['DSF_TEST_WORKBOOK'],'https://demo.example',sweep=False)
            self.assertEqual((app.max_sessions,app.max_starts,app.max_hits),(12,24,240))
            self.assertIsNone(app.prepared_cache);app.close()

    @unittest.skipUnless(os.environ.get('DSF_TEST_WORKBOOK'),'separately supplied official input needed')
    def test_restart_clears_interrupted_preparation_scratch(self):
        from lic_dsf.hosted import HostedApplication
        with tempfile.TemporaryDirectory() as root:
            leftover=Path(root)/'visitors'/'prepared-interrupted'
            leftover.mkdir(parents=True);(leftover/'request.json').write_text('public scratch')
            app=HostedApplication(root,os.environ['DSF_TEST_WORKBOOK'],'https://demo.example',sweep=False)
            try:self.assertFalse(leftover.exists())
            finally:app.close()

if __name__=='__main__':unittest.main(verbosity=2)
