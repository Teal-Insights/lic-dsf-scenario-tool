import copy,io,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'src'))
from lic_dsf import charts


def fixture():
    runs=[]
    for i,label in enumerate(('Scenario A','Scenario B','Scenario C')):
        points=[]
        for j,(metric,title,units,threshold_source) in enumerate(charts.METRICS):
            for k,year in enumerate((2024,2026,2029,2034,2039,2044)):
                baseline=(20+j*8)*(1-.04*k)
                points.append({'metric':metric,'year':year,'units':units,'reference_baseline':baseline,'as_supplied_customized':baseline+1,
                               'scenario':baseline+1+(i-1)*(1+.4*k),'source_cells':{}})
        result={'workbook_sha256':'a'*64,'points':points,'thresholds':{'ext_pv_gdp':40,'ext_pv_exports':180,'ext_ds_exports':15,'ext_ds_revenue':18,'public_pv_gdp':55},
                'evidence':{'exact_excel':'pending','calculation':'computed_unverified'},'warnings':['sampled_years_only'],
                'scenario':{'delta_paths':{'20':[0,-.1,0]},'terms':None},'engine_identity':{'private_path':'/sensitive/source.xlsx'},'notes':'PRIVATE_SENTINEL_X92'}
        runs.append({'id':'run-'+str(i),'scenario_id':str(i),'result_hash':'b'*64,'result':result,'share_label':label,'name':'PRIVATE_SENTINEL_X92'})
    return {'workbook_sha256':'a'*64,'comparator_id':'1','runs':runs}


class ChartsTest(unittest.TestCase):
    def test_unavailable_context_glyphs_refuse_both_export_formats(self):
        c=fixture();c['format']='lic-dsf-comparison-v2'
        c['chart_context']={'workbook_sha256':'a'*64,'label':'分析 — FY2030/31','revision':1}
        before=copy.deepcopy(c)
        # Valid stored Unicode text remains readable, but cannot silently render as boxes.
        self.assertEqual(charts.comparison_summary(c)['chart_context'],c['chart_context'])
        for view in ('standard','briefing'):
            for fmt in ('png','pdf'):
                with self.subTest(view=view,format=fmt),self.assertRaisesRegex(ValueError,'characters unavailable in the export font') as error:
                    charts.render_comparison(c,view,fmt)
                self.assertNotIn('分析',str(error.exception))
        self.assertEqual(c,before)
    def test_supported_accented_label_keeps_selected_font_coverage(self):
        c=fixture();c['chart_context']={'workbook_sha256':'a'*64,'label':'Résumé — Budget: FY2030/31 $x_{2}$ <draft>','revision':1}
        charts._check_context_glyphs(charts.comparison_summary(c))
    def test_context_versions_and_foreign_context_refused(self):
        for version in (None,'lic-dsf-comparison-v1','lic-dsf-comparison-v2'):
            c=fixture()
            if version:c['format']=version
            if version=='lic-dsf-comparison-v2':c['chart_context']={'workbook_sha256':'a'*64,'label':None,'revision':0}
            self.assertEqual(charts.comparison_summary(c)['chart_context'],{'workbook_sha256':'a'*64,'label':None,'revision':0})
        invalid=[{'format':'lic-dsf-comparison-v4'},{'format':None},{'format':'lic-dsf-comparison-v2'},
                 {'chart_context':{'workbook_sha256':'b'*64,'label':'Budget','revision':1}},
                 {'format':'lic-dsf-comparison-v1','chart_context':{'workbook_sha256':'a'*64,'label':' Budget ','revision':1}},
                 {'chart_context':{'workbook_sha256':'a'*64,'label':'Budget','revision':0}},
                 {'chart_context':{'workbook_sha256':'a'*64,'label':'Budget','revision':1,'extra':'ignored?'}}]
        for fields in invalid:
            with self.subTest(fields=fields):
                c=fixture();c.update(fields)
                with self.assertRaises(ValueError):charts.comparison_summary(c)
    def test_context_changes_do_not_change_numerical_summary_or_input(self):
        c=fixture();original=copy.deepcopy(c);before=charts.comparison_summary(c)
        c['format']='lic-dsf-comparison-v2';c['chart_context']={'workbook_sha256':'a'*64,'label':'Budget: FY2030/31','revision':1}
        after=charts.comparison_summary(c)
        self.assertEqual({k:v for k,v in before.items() if k!='chart_context'},{k:v for k,v in after.items() if k!='chart_context'})
        self.assertEqual(c['runs'],original['runs'])
        self.assertEqual(after['chart_context'],c['chart_context'])
    def test_measured_header_preserves_literal_label_and_claims(self):
        import matplotlib.pyplot as plt
        c=fixture();sha=charts.OFFICIAL_EXAMPLE_SHA
        c['workbook_sha256']=sha
        for run in c['runs']:run['result']['workbook_sha256']=sha
        label='$x_{2}$ <Budget> — FY2030/31 '+('W'*51)
        self.assertLessEqual(len(label),80)
        c['chart_context']={'workbook_sha256':sha,'label':label,'revision':1}
        summary=charts.comparison_summary(c)
        for detail in (False,True):
            fig=plt.figure(figsize=(12,10.5) if detail else (14,15.5))
            bottom=charts._header(fig,summary,'briefing',detail=detail)
            artist=next(t for t in fig.texts if t.get_gid()=='chart-context-label')
            self.assertEqual(artist.get_text().replace('\n',''),label)
            self.assertFalse(artist.get_parse_math());self.assertFalse(artist.get_usetex())
            self.assertLessEqual(artist.get_text().count('\n'),2)  # the heading is now the page title (larger type)
            texts=[t.get_text() for t in fig.texts]
            self.assertIn('Workbook SHA-256: '+sha[:12]+'…',texts)
            self.assertIn(charts.ILLUSTRATIVE_DISCLOSURE,texts)
            self.assertTrue(any('Exact Excel comparison pending' in t for t in texts))
            boxes=[t.get_window_extent(fig.canvas.get_renderer()) for t in fig.texts]
            self.assertTrue(all(b.x0>=0 and b.x1<=fig.bbox.width and b.y0>bottom*fig.bbox.height for b in boxes))
            self.assertTrue(all(a.y0>b.y1 for a,b in zip(boxes,boxes[1:])))
            plt.close(fig)
    def test_detail_titles_measured_below_context_and_above_plot(self):
        import matplotlib.pyplot as plt
        c=fixture();sha=charts.OFFICIAL_EXAMPLE_SHA
        c['workbook_sha256']=sha
        c['chart_context']={'workbook_sha256':sha,'label':'W'*80,'revision':1}
        for i,run in enumerate(c['runs']):
            run['result']['workbook_sha256']=sha
            run['share_label']=['W'*40,'M'*40,'Neutral case'][i]
            for p in run['result']['points']:p['scenario']=p['reference_baseline']
        summary=charts.comparison_summary(c)
        for view in ('standard','briefing'):
            fig,ax=plt.subplots(figsize=(12,10.5))
            top=charts._detail_layout(fig,summary,'public_pv_revenue',view)
            ax.set_position([.10,.25,.86,top-.25])
            charts._panel(ax,summary,'public_pv_revenue',view,large=True,heading=False)
            fig.canvas.draw();renderer=fig.canvas.get_renderer()
            boxes=[a.get_window_extent(renderer) for a in fig.texts]
            self.assertTrue(all(a.y0>b.y1 for a,b in zip(boxes,boxes[1:])))
            self.assertTrue(all(b.x0>=0 and b.x1<=fig.bbox.width and b.y0>ax.bbox.y1 for b in boxes))
            title=next(a for a in fig.texts if a.get_gid()=='detail-title')
            self.assertEqual(title.get_text().replace('\n',''),charts._title(summary,'public_pv_revenue',view=='briefing'))
            self.assertFalse(title.get_parse_math())
            if view=='briefing':
                self.assertGreaterEqual(title.get_text().count('\n'),2)
                annotation=next(a for a in ax.texts if a.get_gid()=='comparison-annotation')
                box=annotation.get_window_extent(renderer)
                self.assertLessEqual(box.x1,ax.bbox.x1);self.assertLess(box.y1,ax.bbox.y1)
                self.assertGreater(box.y0,ax.bbox.y0)
                for endpoint in (a for a in ax.texts if hasattr(a,'xy')):
                    endpoint_box=endpoint.get_window_extent(renderer)
                    self.assertLessEqual(endpoint_box.x1,ax.bbox.x1+1)
                    self.assertGreaterEqual(endpoint_box.y0,ax.bbox.y0-1)
                    self.assertLessEqual(endpoint_box.y1,ax.bbox.y1+1)
            else:
                legend=ax.get_legend().get_window_extent(renderer)
                self.assertGreaterEqual(legend.x0,ax.bbox.x0-1)
                self.assertLessEqual(legend.x1,ax.bbox.x1+1)
            plt.close(fig)

    def test_exact_values_comparator_and_no_mutation(self):
        c=fixture();before=copy.deepcopy(c);s=charts.comparison_summary(c)
        self.assertEqual(c,before);self.assertEqual(s['comparator'],'Scenario B')
        row=s['rows'][0]
        self.assertEqual(row['reference_baseline'],20)
        self.assertEqual(row['scenarios'],{'Scenario A':20,'Scenario B':21,'Scenario C':22})
        self.assertEqual(row['differences'],{'Scenario A':-1,'Scenario B':0,'Scenario C':1})
        self.assertNotIn('PRIVATE_SENTINEL_X92',json.dumps(s));self.assertNotIn('/sensitive/',json.dumps(s))
    def test_missing_and_error_are_gaps(self):
        c=fixture();c['runs'][0]['result']['points'][0]['scenario']=None
        c['runs'][2]['result']['points'][0]['scenario']='#VALUE!'
        row=charts.comparison_summary(c)['rows'][0]
        self.assertIsNone(row['scenarios']['Scenario A']);self.assertEqual(row['scenarios']['Scenario C'],'#VALUE!')
        self.assertIsNone(row['differences']['Scenario A']);self.assertIsNone(row['differences']['Scenario C'])
    def test_no_cross_workbook_or_inconsistent_baseline(self):
        for field,value in [('workbook_sha256','b'*64),('baseline',123)]:
            c=fixture()
            if field=='baseline':c['runs'][1]['result']['points'][0]['reference_baseline']=value
            else:c['runs'][1]['result'][field]=value
            with self.assertRaises(ValueError):charts.comparison_summary(c)
    def test_takeaway_uses_observed_comparator_and_neutral_review(self):
        c=fixture();s=charts.comparison_summary(c)
        self.assertEqual(charts._title(s,'ext_pv_gdp',True),'Scenario A is 3.0 pp of GDP below Scenario B in 2044')
        # The same wording for every indicator is asserted by tests/presets.js against the app's text takeaways.
        self.assertEqual([charts._title(s,m[0],True) for m in charts.METRICS],
                         ['Scenario A is 3.0 pp of GDP below Scenario B in 2044','Scenario A is 3.0 pp of exports below Scenario B in 2044',
                          'Scenario A is 3.0 pp of exports below Scenario B in 2044','Scenario A is 3.0 pp of revenue below Scenario B in 2044',
                          'Scenario A is 3.0 pp of GDP below Scenario B in 2044','Scenario A is 3.0 pp of revenue below Scenario B in 2044'])
        self.assertEqual((charts._tenths(0.25),charts._tenths(0.15),charts._tenths(1.05),charts._tenths(2.949)),('0.3','0.1','1.1','2.9'))
        c['runs'][0]['result']['evidence']['calculation']='review_required'
        self.assertEqual(charts._title(charts.comparison_summary(c),'ext_pv_gdp',True),'This comparison needs numerical review')
    def test_both_formats_views_use_same_record(self):
        c=fixture();before=copy.deepcopy(c)
        for view in ('standard','briefing'):
            for fmt,signature in [('png',b'\x89PNG'),('pdf',b'%PDF')]:
                artifact=charts.render_comparison(c,view,fmt)
                self.assertTrue(artifact.startswith(signature));self.assertGreater(len(artifact),10000)
        self.assertEqual(c,before)
    def test_rejects_path_label(self):
        c=fixture();c['runs'][0]['share_label']='/sensitive/source.xlsx'
        with self.assertRaises(ValueError):charts.comparison_summary(c)
    def test_illustrative_disclosure_requires_exact_official_identity(self):
        c=fixture()
        c['provenance']={'disclosure':'Caller text must not establish official provenance'}
        self.assertEqual(charts.comparison_summary(c)['provenance'],{'kind':'user_supplied_workbook','disclosure':None})
        c['workbook_sha256']=charts.OFFICIAL_EXAMPLE_SHA
        for run in c['runs']:run['result']['workbook_sha256']=charts.OFFICIAL_EXAMPLE_SHA
        self.assertEqual(charts.comparison_summary(c)['provenance'],{'kind':'official_illustrative_template','disclosure':charts.ILLUSTRATIVE_DISCLOSURE})
    def test_latest_dot_row_keeps_reference_values_and_explicit_gaps(self):
        c=fixture();c['runs'][0]['result']['points'][5]['scenario']=None
        summary=charts.comparison_summary(c)
        row=charts._latest_row(summary,'ext_pv_gdp')
        self.assertEqual(row['year'],2039)
        self.assertEqual(row['reference_baseline'],c['runs'][0]['result']['points'][4]['reference_baseline'])
        import matplotlib.pyplot as plt
        fig,ax=plt.subplots();charts._dot_panel(ax,summary,'ext_pv_gdp')
        positions=[p.get_offsets().tolist() for p in ax.collections]
        texts=[t.get_text() for t in ax.texts]
        self.assertIn(f'{row["reference_baseline"]:.2f}',texts)
        self.assertIn(f'{row["differences"]["Scenario A"]:+.2f}'.replace('-','\u2212'),texts)
        plt.close(fig)
        for r in summary['rows']:
            if r['metric']=='ext_pv_gdp':r['threshold']=10000
        fig,ax=plt.subplots();charts._dot_panel(ax,summary,'ext_pv_gdp')
        self.assertEqual(positions,[p.get_offsets().tolist() for p in ax.collections]);plt.close(fig)
    def test_curve_end_labels_show_actual_value_and_point_to_observation(self):
        import matplotlib.pyplot as plt
        summary=charts.comparison_summary(fixture());fig,ax=plt.subplots()
        charts._panel(ax,summary,'public_pv_gdp','briefing',large=True)
        labels=[t for t in ax.texts if hasattr(t,'xy')]
        baseline=next(t for t in labels if ' '.join(t.get_text().split()).startswith('Reference baseline:'))
        self.assertEqual(baseline.xy,(2044,41.6))
        self.assertIn('41.60',baseline.get_text())
        self.assertIsNotNone(baseline.arrow_patch)
        plt.close(fig)

if __name__=='__main__':unittest.main()
