"""Retrieval regression checks against the bundled official corpus (no Fortran compilation)."""
import unittest
from pathlib import Path
from tests.regression_index import regression_store

ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless((ROOT/'corpus.catalog.json').is_file(), 'Official corpus not imported')
class ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store=regression_store()
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
        # Anchored to each pattern's in-tree example file so the added
        # nuopc-app-prototypes example corpus cannot crowd it out of the top
        # hits; ranks are not pinned, only that the official ESMF example
        # remains discoverable for its own revision.
        cases=(('NUOPC_DriverAddComp','NUOPC_DriverAddComp ESMF_NUOPCAtmModelEx'),
               ('label_Advertise','label_Advertise ESMF_NUOPCBasicModelEx'),
               ('label_Advance','label_Advance ESMF_NUOPCBasicModelEx'))
        for name,query in cases:
            hits=self.store.search(query,'example',8)
            intree=[hit for hit in hits if 'esmf/NUOPC/examples' in hit['source']]
            self.assertTrue(intree,name)
            children=[hit for hit in intree if hit['parent']]
            result=self.store.get((children or intree)[0]['id'],max_characters=32000)
            self.assertIn(name,result['text'])
            self.assertEqual(result['provenance']['revision'],'bd03a249df907464fdad91b7c43985dedbc472c7')
            if result['parent']:
                self.assertIn('use NUOPC',self.store.get(result['parent'],max_characters=32000)['text'])
    def test_c_reference_sections_retrieve_with_pinned_urls(self):
        hits=self.store.search('ESMC_ArraySpecSet','documentation',8,library='esmf')
        cref=[hit for hit in hits if 'ESMC_crefdoc' in hit['source']]
        self.assertTrue(cref,'ESMC_crefdoc section not discoverable')
        result=self.store.get(cref[0]['id'],include_subsections=True,max_characters=32000)
        self.assertIn('INTERFACE:',result['text'])
        self.assertIn('RETURN VALUE:',result['text'])
        self.assertIn('ESMF_8_9_1/ESMC_crefdoc',result['url'])
        self.assertIn('#SECTION',result['url'])
    def test_context_evidence_categories(self):
        result=self.store.context('NUOPC_DriverAddComp','driver')
        self.assertTrue(result['documentation']);self.assertTrue(result['examples'])
        self.assertTrue(all(h['kind']=='documentation' for h in result['documentation']))
        self.assertTrue(all(h['kind']=='example' for h in result['examples']))
        self.assertEqual(result['application'],[])
    def test_prototypes_are_discoverable_examples(self):
        hits=self.store.search('SetServices','example',8)
        protos=[hit for hit in hits if 'nuopc-app-prototypes' in hit['source']]
        self.assertTrue(protos)
        result=self.store.get(protos[0]['id'])
        self.assertEqual(result['provenance']['revision'],'1645f4471da271e518213ceb574b0ada0ff3a169')
        self.assertIn('1645f4471da2',result['url'])
        readme=[hit for hit in self.store.search('connector options','example',8) if hit['source'].endswith('AtmOcnConOptsProto/README')]
        self.assertTrue(readme)
        config=[hit for hit in self.store.search('ATM_petlist','example',8) if hit['source'].endswith('AtmOcnPetListProto/nuopcRun.config')]
        self.assertTrue(config)
