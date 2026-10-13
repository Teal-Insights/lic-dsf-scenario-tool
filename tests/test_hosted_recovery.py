import unittest
from lic_dsf.hosted import HostedApplication, hosted_page, landing

class RecoveryBoundary(unittest.TestCase):
    def call(self, path, accept='text/html', mode='navigate', host='demo.example'):
        app=HostedApplication.__new__(HostedApplication)
        app.host='demo.example'; app.origin='https://demo.example'
        capture=[]
        env={'REQUEST_METHOD':'GET','PATH_INFO':path,'HTTP_HOST':host,
             'HTTP_ORIGIN':'https://elsewhere.example','HTTP_SEC_FETCH_SITE':'cross-site',
             'HTTP_SEC_FETCH_MODE':mode,'HTTP_SEC_FETCH_DEST':'document','HTTP_ACCEPT':accept}
        body=b''.join(app(env,lambda status,headers:capture.append((status,dict(headers)))))
        return capture[0],body
    def test_navigation_recovers_without_admitting_cross_origin_api(self):
        (status,headers),body=self.call('/app')
        self.assertTrue(status.startswith('403')); self.assertIn('text/html',headers['Content-Type'])
        self.assertIn(b'Return to the start',body); self.assertNotIn(b'X-DSF-Token',body)
        for path,accept,mode,host in [('/api/boot','text/html','navigate','demo.example'),('/app','application/json','navigate','demo.example'),('/app','text/html','cors','demo.example'),('/app','text/html','navigate','wrong.example')]:
            (status,headers),body=self.call(path,accept,mode,host)
            self.assertTrue(status.startswith('403')); self.assertEqual(headers['Content-Type'],'application/json')
    def test_hosted_local_controls_are_inert_and_journal_stays_disabled(self):
        from html.parser import HTMLParser
        class Controls(HTMLParser):
            def __init__(self): super().__init__(); self.stack=[]; self.found={}
            def handle_starttag(self,tag,attrs):
                attrs=dict(attrs)
                if tag in ('fieldset','details','div'): self.stack.append((tag,attrs))
                if attrs.get('id') in ('reasoning','saveReasoning','file'):
                    self.found[attrs['id']]=list(self.stack)
            def handle_endtag(self,tag):
                if tag in ('fieldset','details','div'):
                    for i in range(len(self.stack)-1,-1,-1):
                        if self.stack[i][0]==tag: self.stack=self.stack[:i]; break
        p=Controls(); p.feed(hosted_page().decode())
        for key in ('reasoning','saveReasoning'):
            self.assertTrue(any(tag=='fieldset' and 'disabled' in attrs for tag,attrs in p.found[key]))
            self.assertTrue(any('hidden' in attrs and 'inert' in attrs for tag,attrs in p.found[key]))
        self.assertTrue(any('hidden' in attrs and 'inert' in attrs for tag,attrs in p.found['file']))
    def test_entry_primary_action_precedes_expanded_service_details(self):
        page=landing(25,50).decode()
        self.assertLess(page.index('id="begin"'),page.index('<details>'))
        self.assertIn('25 simultaneous visits and 50 new visits',page)
        self.assertIn('30 completed exports',page)
        self.assertNotIn('MAX_VISITS',page)

    def test_entry_download_link_targets_current_alpha2_release(self):
        page=landing().decode()
        self.assertIn('<a href="https://github.com/Teal-Insights/lic-dsf-scenario-tool/releases/tag/v0.1.0-alpha.2">Download the local app for your own workbook</a>',page)

    def test_landing_callout(self):
        page = landing().decode()
        self.assertIn('What this site is', page)
        self.assertIn('runs locally on your own computer', page)
        self.assertIn('design feedback', page)
        self.assertIn('mailto:lte@tealinsights.com', page)
        self.assertIn('published by the World Bank', page)
        self.assertLess(page.index('What this site is'), page.index('id="begin"'))
        self.assertLess(page.index('published by the World Bank'), page.index('id="begin"'))
        self.assertLess(page.index('Not an IMF or World Bank product'), page.index('id="begin"'))
        self.assertLess(page.index('id="begin"'), page.index('<details class="limits">'))
        self.assertIn('does not represent any actual country', page)  # country-name guard: tests/test_no_country_name.py
        self.assertIn('Illustrative', page)

    def test_visit_box_is_short_and_names_the_local_tool(self):
        page = hosted_page().decode()
        self.assertNotIn('online experiment', page.lower())
        self.assertNotIn('online visit', page.lower())
        aside = page[page.index('<aside class="card">'):page.index('</aside>')]
        self.assertTrue(aside.startswith('<aside class="card"><strong>Illustrative online version</strong>'))
        self.assertIn('href="https://github.com/Teal-Insights/lic-dsf-scenario-tool"', aside)
        self.assertIn('meant to run locally on your own computer', aside)
        self.assertIn('Macronia', aside)
        self.assertIn('mailto:lte@tealinsights.com', aside)
        # Service detail sits in a closed disclosure; the delete button and the export wait panel stay outside it.
        limits = aside[aside.index('<details class="help">'):aside.index('</details>')]
        self.assertIn('final slot is reserved', limits)
        self.assertNotIn('open', aside[aside.index('<details class="help"'):aside.index('<summary>', aside.index('<details class="help"'))])
        self.assertNotIn('deleteVisit', limits)
        self.assertNotIn('exportWaitPanel', limits)

    def test_edition_title_and_note_are_short_and_plain(self):
        from lic_dsf.hosted import EDITION_NOTE, EDITION_TITLE
        self.assertEqual(EDITION_TITLE, 'LIC-DSF Scenario Tool: illustrative online version')
        self.assertLess(len(EDITION_NOTE), 200)
        self.assertNotIn('experiment', EDITION_NOTE)

    def test_upload_step_explains_the_desktop_version(self):
        page = hosted_page().decode()
        step1 = page[page.index('<section id="upload"'):page.index('</section>', page.index('<section id="upload"'))]
        self.assertIn('In the desktop version, this is where you would upload your own completed DSA workbook. '
                      'This online version uses the official illustrative example instead, so nobody uploads private data.', step1)
        self.assertNotIn('.xlsm">Download the supported template</a>', page)

    def test_landing_names_the_local_tool_and_macronia(self):
        page = landing().decode()
        callout = page[page.index('What this site is'):page.index('id="begin"')]
        self.assertIn('<a href="https://github.com/Teal-Insights/lic-dsf-scenario-tool">LIC-DSF Scenario Tool</a>', callout)
        self.assertIn('illustrative online version', callout)
        self.assertIn('Macronia', callout)
        self.assertIn('does not represent any actual country', callout)
