"""In-process WSGI boundary tests; real official input supplied separately."""
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from lic_dsf.hosted import HostedApplication, OFFICIAL_EXAMPLE_SHA, MAX_REQUESTS, MAX_SESSIONS

BOOK = os.environ.get('DSF_TEST_WORKBOOK')
class Client:
    def __init__(self, app):
        self.app, self.cookie, self.token = app, '', ''
    def call(self, path, data=None, **overrides):
        route, _, query = path.partition('?')
        body = json.dumps(data, separators=(',', ':')).encode() if data is not None else b''
        env = dict(REQUEST_METHOD='POST' if data is not None else 'GET', PATH_INFO=route, QUERY_STRING=query,
            HTTP_HOST='demo.example', HTTP_ORIGIN='https://demo.example', HTTP_COOKIE=self.cookie,
            HTTP_X_DSF_TOKEN=self.token, CONTENT_TYPE='application/json', CONTENT_LENGTH=str(len(body)))
        env['wsgi.input'] = io.BytesIO(body); env.update(overrides)
        capture = []
        result = b''.join(self.app(env, lambda status, headers: capture.append((status, dict(headers)))))
        status, headers = capture[0]
        if 'Set-Cookie' in headers:
            self.cookie = headers['Set-Cookie'].split(';')[0]
        if headers['Content-Type'] == 'application/json':
            result = json.loads(result)
        return int(status[:3]), result, headers
    def enter(self):
        assert self.call('/api/session', {'accept': True})[0] == 200
        code, data, _ = self.call('/api/boot'); assert code == 200
        self.token = data['token']; return self

@unittest.skipUnless(BOOK, 'Supply the exact official workbook outside the source tree.')
class HostedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.now = 0
        cls.app = HostedApplication(cls.tmp.name, BOOK, 'https://demo.example', clock=lambda: cls.now, sweep=False)
    @classmethod
    def tearDownClass(cls):
        cls.app.close(); cls.tmp.cleanup()
    def test_boundaries(self):
        a, b = Client(self.app).enter(), Client(self.app).enter()
        self.assertNotEqual(a.cookie, b.cookie); self.assertNotEqual(a.token, b.token)
        for route in ['/api/upload','/api/import','/api/reasoning','/api/upload?other=1']:
            self.assertEqual(a.call(route, {'sentinel': 'DO_NOT_STORE'})[0], 404)
        self.assertEqual(a.call('/api/example', {}, HTTP_ORIGIN='https://other.example')[0], 403)
        self.assertEqual(a.call('/api/example', {}, HTTP_X_DSF_TOKEN=b.token)[0], 403)
        self.assertEqual(a.call('/api/example', {}, CONTENT_LENGTH='131073')[0], 413)
        self.assertEqual(a.call('/api/example', {})[0], 200)
        code, context, _ = a.call('/api/workbook?sha='+OFFICIAL_EXAMPLE_SHA)
        self.assertEqual(code, 200)
        code, saved, _ = a.call('/api/save', {'workbook_sha':OFFICIAL_EXAMPLE_SHA, 'name':'Synthetic visitor A', 'share_label':'Control','definition':context['zero']})
        self.assertEqual(code, 200, saved)
        sid = saved['id']
        self.assertEqual(b.call('/api/scenario?id='+sid)[0], 400)
        self.assertEqual(b.call('/api/calculate', {'scenario_id':sid})[0], 400)
        self.assertEqual(b.call('/api/job?id=unknown')[1]['status'], 'interrupted')
        self.assertEqual(b.call('/api/workbook?sha='+'f'*64)[0], 400)
        ws = self.app.sessions[a.cookie.split('=',1)[1]]
        ws.requests = MAX_REQUESTS
        self.assertEqual(a.call('/api/delete', {})[0], 200)
        self.assertFalse(ws.directory.exists())
        self.assertEqual(a.call('/api/boot')[0], 401)
        for p in Path(self.tmp.name).rglob('*'):
            if p.is_file(): self.assertNotIn(b'DO_NOT_STORE', p.read_bytes())
    def test_expiry_capacity_restart(self):
        self.app.expire()
        clients=[]
        while len(self.app.sessions) < MAX_SESSIONS:
            clients.append(Client(self.app).enter())
        self.assertEqual(Client(self.app).call('/api/session', {'accept': True})[0],503)
        type(self).now += 3601; self.app.expire()
        self.assertEqual(len(self.app.sessions),0)
        self.assertEqual(list(self.app.visitors.iterdir()),[])
        c=Client(self.app).enter(); self.app.close()
        type(self).app=HostedApplication(self.tmp.name,BOOK,'https://demo.example',sweep=False)
        self.assertEqual(Client(self.app).call('/api/boot',HTTP_COOKIE=c.cookie)[0],401)
        self.assertEqual(list(self.app.visitors.iterdir()),[])

class LifecycleRegressionTests(unittest.TestCase):
    def test_queued_cancellation_releases_global_capacity(self):
        from concurrent.futures import Future
        import threading
        from types import SimpleNamespace
        from lic_dsf.hosted import HostedWorkspace
        class Queued:
            def submit(self, fn):
                self.future = Future(); return self.future
            def shutdown(self, **kwargs): self.future.cancel()
        with tempfile.TemporaryDirectory() as root:
            ws = HostedWorkspace.__new__(HostedWorkspace)
            ws.owner = SimpleNamespace(compute=threading.BoundedSemaphore(1), prepared_cache=None)
            ws.store = SimpleNamespace(get_scenario=lambda _: {})
            ws.jobs, ws.executor, ws.child = {}, Queued(), None
            ws.directory = Path(root)/'visitor'; ws.directory.mkdir()
            ws.start_calculation('case'); ws.close()
            self.assertTrue(ws.owner.compute.acquire(blocking=False))
            self.assertFalse(ws.directory.exists())

    def test_cache_excludes_all_visitor_fields(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        from lic_dsf.hosted import HostedWorkspace
        from lic_dsf.app import Workspace
        ws=HostedWorkspace.__new__(HostedWorkspace)
        ws.owner=SimpleNamespace(context_cache=None)
        ws.path=lambda _: None
        ws.store=SimpleNamespace(list_scenarios=lambda _: [], get_chart_context=lambda _: {'label':None})
        with patch.object(Workspace, 'context', return_value={'inspection':{}, 'scenarios':[{'secret':'synthetic'}], 'chart_context':{'label':'synthetic'}}):
            ws.context('example')
        self.assertEqual(ws.owner.context_cache, {'inspection':{}})

    def test_deployment_excludes_generated_bytecode(self):
        text=(Path(__file__).parents[1]/'.dockerignore').read_text()
        self.assertGreater(text.index('**/__pycache__'), text.index('!src/**'))
        self.assertGreater(text.index('**/*.pyc'), text.index('!src/**'))

    def test_cleanup_failure_is_fail_closed_and_retryable(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        from lic_dsf.hosted import HostedApplication
        import threading, subprocess
        app = HostedApplication.__new__(HostedApplication)
        app.lock = threading.RLock(); app.origin = 'https://demo.example'; app.host = 'demo.example'
        app.sessions = {'key':SimpleNamespace(created=0, close=lambda: None)}
        app.clock = lambda: 3601
        with patch.object(app.sessions['key'], 'close', side_effect=subprocess.TimeoutExpired('owned-child',5)):
            code, data, headers = Client(app).call('/api/boot')
            self.assertEqual(code,503); self.assertTrue(app.cleanup_failed)
        app.expire()
        self.assertFalse(app.cleanup_failed); self.assertEqual(app.sessions,{})

@unittest.skipUnless(BOOK, 'Supply the exact official workbook separately.')
class SuccessorBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.now=0
        self.app=HostedApplication(self.tmp.name,BOOK,'https://demo.example',clock=lambda:self.now,sweep=False)
    def tearDown(self):
        self.app.close();self.tmp.cleanup()
    def test_public_navigation_exception_is_stateless_and_narrow(self):
        c=Client(self.app)
        headers={'HTTP_ORIGIN':'https://external.example','HTTP_SEC_FETCH_SITE':'cross-site',
                 'HTTP_SEC_FETCH_MODE':'navigate','HTTP_SEC_FETCH_DEST':'document'}
        code,body,reply=c.call('/',**headers)
        self.assertEqual(code,200);self.assertIn(b'Start an illustrative visit',body)
        self.assertNotIn('Set-Cookie',reply);self.assertEqual(self.app.sessions,{})
        self.assertEqual(c.call('/api/boot',**headers)[0],403)
        self.assertEqual(c.call('/api/session',{'accept':True},**headers)[0],403)
        self.assertEqual(c.call('/',**{**headers,'HTTP_HOST':'attacker.example'})[0],403)
        self.assertEqual(c.call('/',**{**headers,'HTTP_SEC_FETCH_MODE':'cors'})[0],403)
        self.assertEqual(c.call('/',**{**headers,'HTTP_SEC_FETCH_DEST':'iframe'})[0],403)
        c.enter()
        self.assertEqual(c.call('/api/example',{},**headers)[0],403)
    def test_expired_app_is_html_but_apis_remain_json(self):
        c=Client(self.app).enter();self.now=3601
        code,body,headers=c.call('/app')
        self.assertEqual(code,401);self.assertIn('text/html',headers['Content-Type'])
        self.assertIn(b'href="/"',body);self.assertEqual(self.app.sessions,{})
        self.assertEqual(c.call('/api/boot')[2]['Content-Type'],'application/json')
    def test_hostile_json_is_bounded_before_mutation(self):
        c=Client(self.app).enter();ws=next(iter(self.app.sessions.values()))
        for route in ['/api/save','/api/compare','/api/export','/api/example','/api/delete']:
            for payload in [b'{',b'{"x":NaN}',b'{"x":1e9999}',b'{"x":1,"x":2}',b'[]',b'{"x":'+b'['*1000+b'0'+b']'*1000+b'}',b'{"x":"\xff"}']:
                code,_,_=c.call(route,{},CONTENT_LENGTH=str(len(payload)),**{'wsgi.input':io.BytesIO(payload)})
                self.assertEqual(code,400,(route,payload[:30]))
        self.assertEqual(ws.mutations,0);self.assertEqual(ws.exports,0);self.assertFalse(ws.closed)
        self.assertEqual(c.call('/api/example',{})[0],200)

class SuccessorRegressionTests(unittest.TestCase):
    def test_bounded_json_strings_and_boundary(self):
        from lic_dsf.hosted import bounded_json
        value={'text':'[{'+chr(34)+chr(92)+'}]'*100,'n':1.25}
        self.assertEqual(bounded_json(json.dumps(value).encode()),value)
        self.assertEqual(bounded_json(b'{"x":'+b'['*31+b'0'+b']'*31+b'}')['x'][0][0][0][0][0] is not None,True)
        with self.assertRaises(ValueError):bounded_json(b'{"x":'+b'['*32+b'0'+b']'*32+b'}')
    def test_hosted_copy_and_template_drift(self):
        from lic_dsf.hosted import hosted_page, landing
        from unittest.mock import patch
        page=hosted_page().decode()
        for forbidden in ['Local workspace','Upload your completed workbook to get started.','Go to upload','calculations then run locally.','Scenarios are saved separately on this computer.']:
            self.assertNotIn(forbidden,page)
        self.assertIn('final slot is reserved',page)
        # S5: the baseline explanation sits beside the charts; no 'verification pending' copy online.
        guide=page.index('id="comparisonGuide"')
        self.assertLess(guide,page.index('id="chartPair"'))
        self.assertIn('No investment, the comparison case for the teaching cases, uses this example’s customized projections. Reference baseline is shown for context only: the gap between them reflects starting assumptions, not the investment.',page)
        self.assertNotIn('verification pending',page)
        self.assertIn('12 simultaneous visits',landing().decode())
        source=(Path(__file__).parents[1]/'src/lic_dsf/web.html').read_text(encoding='utf-8')
        with patch('pathlib.Path.read_text',return_value=source.replace('Local workspace','Unexpected local copy')):
            with self.assertRaisesRegex(ValueError,'template changed'):hosted_page()
    def workspace(self):
        from lic_dsf.hosted import HostedWorkspace
        from types import SimpleNamespace
        import threading
        ws=HostedWorkspace.__new__(HostedWorkspace)
        ws.owner=SimpleNamespace(compute=threading.BoundedSemaphore(1), prepared_cache=None)
        ws.exports=0;ws.jobs={};ws.closed=False;ws.store=SimpleNamespace(get_scenario=lambda sid:{})
        ws._render_export=lambda comparison,data:(b'output','application/zip','packet.zip')
        return ws
    def test_reservation_counts_all_formats_and_failures_preserve_it(self):
        ws=self.workspace()
        for _ in range(29):ws.bounded_export({}, {'format':'json'})
        for fmt in ['json','svg','png','pdf','xlsx']:
            with self.assertRaisesRegex(ValueError,'reserved final slot'):ws.bounded_export({}, {'format':fmt})
        self.assertEqual(ws.exports,29)
        def fail(*_):raise ValueError('render failure')
        ws._render_export=fail
        with self.assertRaisesRegex(ValueError,'render failure'):ws.bounded_export({}, {'format':'zip'})
        self.assertEqual(ws.exports,29)
        self.assertTrue(ws.owner.compute.acquire(False));ws.owner.compute.release()
        ws._render_export=lambda *_:(b'packet','application/zip','packet.zip')
        ws.bounded_export({}, {'format':'zip'});self.assertEqual(ws.exports,30)
        with self.assertRaisesRegex(ValueError,'all 30'):ws.bounded_export({}, {'format':'zip'})
    def test_heavy_work_exclusion_and_busy_retry(self):
        import threading
        ws=self.workspace()
        self.assertTrue(ws.owner.compute.acquire(False))
        with self.assertRaisesRegex(ValueError,'retry shortly'):ws.bounded_export({}, {'format':'zip'})
        self.assertEqual(ws.exports,0);ws.owner.compute.release()
        entered=threading.Event();release=threading.Event()
        def render(*_):
            entered.set();release.wait(5)
            return b'packet','application/zip','packet.zip'
        ws._render_export=render
        thread=threading.Thread(target=lambda:ws.bounded_export({}, {'format':'zip'}));thread.start()
        try:
            self.assertTrue(entered.wait(2))
            with self.assertRaisesRegex(ValueError,'retry shortly'):ws.start_calculation('case')
            self.assertFalse(ws.owner.compute.acquire(False))
        finally:release.set();thread.join(5)
        self.assertFalse(thread.is_alive());self.assertEqual(ws.exports,1)
        self.assertTrue(ws.owner.compute.acquire(False));ws.owner.compute.release()

if __name__ == '__main__': unittest.main()
