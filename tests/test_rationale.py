import copy
import json
import sqlite3
import unittest
from test_store import StoreTests, store
from test_charts import fixture
from lic_dsf import charts
from lic_dsf.rationale import normalize_rationale, rationale_entries


class RationaleStoreTests(StoreTests):
    def test_version2_migration_keeps_private_journals_and_runs(self):
        self.s.record_run(self.case['id'], self.result(), expected_revision=1)
        self.s.add_reasoning(self.case['id'], 'PRIVATE JOURNAL NEVER SHARED')
        with sqlite3.connect(self.s.database) as db:
            db.execute('DROP TABLE shared_rationale')
            db.execute("UPDATE metadata SET value='2' WHERE key='schema_version'")
            before={table:list(db.execute('SELECT * FROM '+table)) for table in ['revisions','runs','reasoning','chart_context']}
        self.s=store.ScenarioStore(self.s.directory)
        self.assertEqual(self.s.get_scenario(self.case['id'])['shared_rationale'], {})
        self.assertEqual(self.current()['result'], self.result())
        with sqlite3.connect(self.s.database) as db:
            for table,rows in before.items():self.assertEqual(list(db.execute('SELECT * FROM '+table)),rows)
        self.assertNotIn('PRIVATE JOURNAL', json.dumps(self.current()))

    def test_notes_revision_reopen_and_preserved_on_legacy_save(self):
        notes={'11':'Assumed fiscal change.\nSource: analyst judgment.'}
        first=self.s.save_scenario(self.sha,'Local',self.definition,shared_rationale=notes)
        self.assertEqual(first['shared_rationale'],notes)
        self.assertEqual(first['definition'],self.definition)
        reopened=store.ScenarioStore(self.s.directory).get_scenario(first['id'])
        self.assertEqual(reopened,first)
        second=self.s.save_scenario(self.sha,'Local',self.definition,scenario_id=first['id'],expected_revision=1)
        self.assertEqual(second['shared_rationale'],notes)
        third=self.s.save_scenario(self.sha,'Local',self.definition,scenario_id=first['id'],expected_revision=2,shared_rationale={})
        self.assertEqual(third['shared_rationale'],{})
        with sqlite3.connect(self.s.database) as db:
            self.assertEqual(json.loads(db.execute('SELECT notes FROM shared_rationale WHERE scenario_id=? AND revision=1',(first['id'],)).fetchone()[0]),notes)

    def test_invalid_notes_fail_without_writes(self):
        before=self.s.database.read_bytes()
        for notes in [{'private_journal':'not an input'},{'20':'x'*1501},{'20':False},{'20':'bad\x00text'}]:
            with self.assertRaises(ValueError):self.s.save_scenario(self.sha,'Local',self.definition,shared_rationale=notes)
            self.assertEqual(self.s.database.read_bytes(),before)

    def test_corruption_and_deleted_metadata_refused(self):
        with sqlite3.connect(self.s.database) as db:
            db.execute("UPDATE shared_rationale SET notes=?",(json.dumps({'11':'tampered'}),))
        with self.assertRaises(store.StaleResult):self.s.get_scenario(self.case['id'])
        with sqlite3.connect(self.s.database) as db:db.execute('DELETE FROM shared_rationale')
        with self.assertRaises(store.StaleResult):self.s.get_scenario(self.case['id'])

    def test_metadata_edit_keeps_current_result_without_recalculation(self):
        # Round 002 contract change: explanation-only and label-only revisions keep the
        # calculation of the revision they were saved from; numerical edits still invalidate it.
        self.s.record_run(self.case['id'],self.result(),expected_revision=1)
        self.s.save_scenario(self.sha,'Local',self.definition,scenario_id=self.case['id'],expected_revision=1,shared_rationale={'11':'Public reasoning'})
        current=self.current()
        self.assertEqual(current['revision'],2)
        self.assertEqual(current['shared_rationale'],{'11':'Public reasoning'})
        self.assertEqual(current['result'],self.result())
        edited={'delta_paths':{'11':[0,3]},'terms':None}
        self.s.save_scenario(self.sha,'Local',edited,scenario_id=self.case['id'],expected_revision=2,shared_rationale={'11':'Public reasoning'})
        with self.assertRaises(store.StaleResult):self.current()


class RationaleContractTests(unittest.TestCase):
    def test_annex_continuations_keep_driver_context_and_every_body_line(self):
        import matplotlib.pyplot as plt
        summary=charts.comparison_summary(fixture())
        body=[f'Assumption line {i:02d}.' for i in range(70)]
        summary['assumptions']=[{'scenario':'Illustrative case','shared_explanations':[
            {'label':'Primary expenditure','changed':True,'text':'\n'.join(body)},
            {'label':'Financing terms','changed':False,'text':'Financing explanation.'}]}]
        pages=[]
        class Sink:
            def savefig(self,fig):
                pages.append([(t.get_text(),t.get_fontweight()) for t in fig.texts
                              if t.get_fontsize()==10 and t.get_text().startswith(
                                  ('Assumption line ', 'Financing explanation.',
                                   'Primary expenditure', 'Financing terms'))])
        charts._rationale_pages(Sink(),summary,plt,'briefing')
        self.assertGreater(len(pages),1)
        self.assertTrue(any('(continued)' in text for page in pages for text,_ in page))
        collected=[text for page in pages for text,weight in page if weight!='bold' and text]
        self.assertEqual(collected,body+['Financing explanation.'])
        for page in pages:
            nonempty=[(text,weight) for text,weight in page if text]
            self.assertEqual(nonempty[0][1],'bold')
            for i,(text,weight) in enumerate(nonempty):
                if weight=='bold':
                    self.assertLess(i+1,len(nonempty),'A driver heading must not be orphaned')
                    self.assertNotEqual(nonempty[i+1][1],'bold')

    def test_normalization_missing_and_unchanged_notes(self):
        self.assertEqual(normalize_rationale({'20':'  Cafe\u0301\nmodel ', '13':' '}),{'20':'Café\nmodel'})
        entries=rationale_entries({'delta_paths':{'20':[0,-1]},'terms':None},{'13':'Why spending is unchanged'})
        self.assertEqual([e['driver'] for e in entries],['13','20'])
        self.assertFalse(entries[0]['changed']);self.assertEqual(entries[1]['text'],'No explanation provided.')

    def test_summary_only_copies_deliberately_shared_notes(self):
        c=fixture();before=copy.deepcopy(c)
        c['runs'][0]['shared_rationale']={'20':'EXPLICIT SHARED EXPLANATION'}
        summary=charts.comparison_summary(c)
        self.assertIn('EXPLICIT SHARED EXPLANATION',json.dumps(summary))
        self.assertNotIn('PRIVATE_SENTINEL',json.dumps(summary))
        self.assertEqual(summary['rows'],charts.comparison_summary(before)['rows'])
        self.assertEqual(c['runs'][0]['result'],before['runs'][0]['result'])

    def test_v3_requires_explicit_explanation_metadata(self):
        c=fixture();c['format']='lic-dsf-comparison-v3'
        c['chart_context']={'workbook_sha256':c['workbook_sha256'],'label':None,'revision':0}
        with self.assertRaisesRegex(ValueError,'Shared explanations are required'):
            charts.comparison_summary(c)
        for run in c['runs']:run['shared_rationale']={}
        self.assertEqual(len(charts.comparison_summary(c)['assumptions']),3)

    def test_pdf_font_failure_is_explicit_json_text_preserved(self):
        c=fixture();c['runs'][0]['shared_rationale']={'20':'分析'}
        summary=charts.comparison_summary(c)
        self.assertEqual(summary['assumptions'][0]['shared_explanations'][0]['text'],'分析')
        with self.assertRaisesRegex(ValueError,'shared explanation contains characters unavailable'):
            charts._check_rationale_glyphs(summary)

if __name__=='__main__':unittest.main()
