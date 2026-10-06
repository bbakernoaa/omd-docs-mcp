"""Retrieval regression checks against the bundled official corpus (no Fortran compilation)."""
import tempfile
import unittest
from pathlib import Path
from knowledge import build, Knowledge

ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless((ROOT/'corpus.json').is_file(), 'Official corpus not imported')
class ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.db=Path(cls.temp.name)/'index.sqlite3'
        build(ROOT/'corpus.json',cls.db);cls.store=Knowledge(cls.db)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_api_overloads_have_signatures_arguments_and_urls(self):
        for name in ('NUOPC_CompSpecialize','NUOPC_DriverAddComp','NUOPC_Advertise'):
            hits=self.store.search(name,'documentation',6)
            own=[hit for hit in hits if name in hit['title']]
            self.assertGreaterEqual(len(own),2)
            for hit in own:
                result=self.store.get(hit['id'],include_subsections=True)
                self.assertIn('INTERFACE:',result['text'])
                self.assertIn('ARGUMENTS:',result['text'])
                self.assertIn('ESMF_8_9_1',result['url'])
                self.assertIn('#',result['url'])
    def test_real_driver_and_cap_patterns_and_commit(self):
        for name in ('NUOPC_DriverAddComp','label_Advertise','label_Advance'):
            hits=self.store.search(name,'example',6)
            self.assertTrue(hits)
            result=self.store.get(hits[0]['id'])
            self.assertIn(name,result['text'])
            self.assertEqual(result['provenance']['revision'],'bd03a249df907464fdad91b7c43985dedbc472c7')
            if result['parent']:
                self.assertIn('use NUOPC',self.store.get(result['parent'])['text'])
    def test_context_evidence_categories(self):
        result=self.store.context('NUOPC_DriverAddComp','driver')
        self.assertTrue(result['documentation']);self.assertTrue(result['examples'])
        self.assertTrue(all(h['kind']=='documentation' for h in result['documentation']))
        self.assertTrue(all(h['kind']=='example' for h in result['examples']))
        self.assertEqual(result['application'],[])
