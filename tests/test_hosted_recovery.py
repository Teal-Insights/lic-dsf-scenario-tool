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
        self.assertIn('In the desktop app, this is where you would upload your own completed DSA workbook, or reopen one saved on your computer. '
                      'This web version cannot do that, so it uses the official illustrative example instead: the most recent version of the', step1)
        self.assertIn('new-lic-dsf-template', step1)
        self.assertNotIn('.xlsm">Download the supported template</a>', page)

    def test_landing_names_the_local_tool_and_macronia(self):
        page = landing().decode()
        callout = page[page.index('What this site is'):page.index('id="begin"')]
        self.assertIn('<a href="https://github.com/Teal-Insights/lic-dsf-scenario-tool">LIC-DSF Scenario Tool</a>', callout)
        self.assertIn('illustrative online version', callout)
        self.assertIn('Macronia', callout)
        self.assertIn('relabelled here as a fictional country, Macronia', callout)
        self.assertIn('does not represent any actual country', callout)

    def test_first_steps_are_guided(self):
        page = hosted_page().decode()
        def before(a, b): self.assertLess(page.index(a), page.index(b), (a, b))
        self.assertRegex(page, r'id="exampleButton"[^>]*data-hint="[^"]*Macronia[^"]*step 2')
        self.assertIn('<h2 tabindex="-1">2. Review the baseline</h2>', page)
        self.assertIn('Make sure the tool read the file correctly before you change anything', page)
        self.assertIn('Optional. Ticking it marks step 2 as done; it changes no numbers.', page)
        self.assertIn("'In step 3, load a teaching case (or edit inputs), then Save scenario and Calculate.'", page)
        self.assertIn("'Optional: tick the box in step 2 once you have looked over the Macronia baseline. Then save and calculate a case in step 3.'", page)
        self.assertIn("'Load a teaching case'", page)
        self.assertIn("'Load teaching case 1'", page)
        self.assertIn('<strong>New here?</strong>', page)
        before('<strong>New here?</strong>', 'Customized Scenario</strong> tabs.')
        self.assertIn("status('Teaching case loaded but not saved. Next: click Save scenario in the bar at the bottom of the screen, then Calculate and show results.'", page)
        self.assertNotIn('few seconds', page)  # no unmeasured time promises
        self.assertNotIn('one to two minutes', page)
        self.assertNotIn('startup results', page)
        self.assertIn('Delete my work and return to the start', page)
        # After one calculated case every difference is zero: point to teaching case 2 before any download.
        self.assertIn('In step 3, load teaching case 2, then Save and Calculate it; it joins this comparison automatically.', page)
        self.assertNotIn('select both in step 4', page)
        self.assertIn("'Optional, not ticked'", page)
        self.assertNotIn('Not re-checked this visit', page)
        self.assertNotIn('Download the briefing once at least two cases are compared', page)
        self.assertIn('Only one case is compared, so every difference is zero: load and calculate teaching case 2 in step 3 before downloading.', page)
        self.assertIn('Only one case is compared, so every difference is zero. Load and calculate teaching case 2 in step 3 before downloading.', page)
        landing_page = landing().decode()
        self.assertIn('load and calculate the three teaching cases', landing_page)
        self.assertLess(landing_page.index('You will: load the example'), landing_page.index('id="begin"'))

    def test_walkthrough_says_what_each_step_is_for(self):
        page = hosted_page().decode()
        main = page[page.index('<main'):page.index('<section id="methodology"')]
        methodology = page[page.index('<section id="methodology"'):page.index('</section>', page.index('<section id="methodology"'))]
        # Fine print and the generic glossary live in How this tool works, not in the main flow.
        for text in ('Early-stage preview', 'What do PV, PPG and percentage points mean?', 'fresh Excel verification remains pending'):
            self.assertNotIn(text, main)
        self.assertIn('<summary>Notes, limits and verification</summary>', methodology)
        self.assertIn('<summary>Glossary</summary>', methodology)
        self.assertIn('Early-stage preview', methodology)
        # Each step says what it is for.
        self.assertEqual(main.count('class="step-purpose"'), 5)
        # Step 3: a numbered path, a Save/Calculate bar that stays in view, and plain unsaved-edit wording.
        self.assertIn('<ol class="teach-steps"', main)
        self.assertRegex(page, r'\.save-bar\{[^}]*position:sticky;bottom:0')
        self.assertIn('This draft is not saved yet. Click Save scenario (bottom of step 3) to keep it, or Discard unsaved edits (top of step 3) to drop it. Then try again.', page)
        self.assertNotIn('before switching', page)

