import json
import tempfile
import unittest
from pathlib import Path
from knowledge import Knowledge, build, markup_sections

RST='''KokkosBlas::gemm
################

.. code:: c++

   void gemm(const char transA[], const char transB[]);

Parameters
==========

transA controls the transpose operation.

Example
=======

.. literalinclude:: ../../examples/gemm.cpp
'''

class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        (self.root/'api.rst').write_text(RST)
        (self.root/'gemm.cpp').write_text('void example() { KokkosBlas::gemm("N", "N"); }\n')
        entries=[]
        for library,version in [('kokkos','snapshot-test'),('kokkos-kernels','5.2.2'),('esmf','8.9.1')]:
            entries.append({'name':'same-name','path':'api.rst','library':library,'version':version,'kind':'documentation'})
        entries.append({'name':'includes','path':'gemm.cpp','library':'kokkos-kernels','version':'5.2.2','kind':'example'})
        self.manifest=self.root/'corpus.json';self.manifest.write_text(json.dumps({'sources':entries}))
        self.db=self.root/'index.sqlite3';build(self.manifest,self.db);self.store=Knowledge(self.db)
    def tearDown(self):self.temp.cleanup()
    def test_library_isolation(self):
        for library in ('esmf','kokkos','kokkos-kernels'):
            hits=self.store.search('KokkosBlas::gemm','documentation',library=library)
            self.assertTrue(hits);self.assertTrue(all(hit['library']==library for hit in hits))
    def test_rst_section_code_and_include(self):
        hit=self.store.search('KokkosBlas::gemm','documentation',library='kokkos-kernels')[0]
        result=self.store.get(hit['id'],include_subsections=True)
        self.assertIn('void gemm(',result['text']);self.assertIn('transA controls',result['text'])
        self.assertEqual(len(result['included_code']),1)
        self.assertIn('void example()',self.store.get(result['included_code'][0]['id'])['text'])
    def test_multiple_versions_require_explicit_choice(self):
        manifest=json.loads(self.manifest.read_text())
        manifest['sources'].append({'name':'same-name','path':'api.rst','library':'kokkos-kernels','version':'5.1.0','kind':'documentation'})
        self.manifest.write_text(json.dumps(manifest));build(self.manifest,self.db)
        with self.assertRaises(ValueError):self.store.search('gemm',library='kokkos-kernels')
        hits=self.store.search('gemm',library='kokkos-kernels',version='5.2.2')
        self.assertTrue(all(h['version']=='5.2.2' for h in hits))
    def test_markdown_fence_not_heading(self):
        text='# API\n```cpp\n# not-a-heading\nvoid x();\n```\n## Arguments\nint x\n'
        units=markup_sections(text,'api.md','','.md')
        self.assertEqual([u['title'] for u in units],['API','Arguments'])
        self.assertIn('# not-a-heading',units[0]['text'])

ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless((ROOT/'kokkos-lock.json').exists(),'Kokkos corpus not imported')
class KokkosReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.db=Path(cls.temp.name)/'index.sqlite3'
        build(ROOT/'corpus.json',cls.db);cls.store=Knowledge(cls.db)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_core_api_section(self):
        hit=self.store.search('Kokkos::parallel_for','documentation',library='kokkos')[0]
        result=self.store.get(hit['id'],include_subsections=True)
        self.assertIn('Kokkos::parallel_for',result['text'])
        self.assertIn('functor',result['text'])
        self.assertTrue(result['version'].startswith('snapshot-'))
        self.assertIn(result['provenance']['revision'],result['url'])
    def test_view_parent_section_is_discoverable(self):
        hit=self.store.search('Kokkos::View','documentation',library='kokkos')[0]
        result=self.store.get(hit['id'],include_subsections=True)
        self.assertEqual(hit['title'],'``View``')
        self.assertIn('cpp:class::',result['text'])
        self.assertIn('DataType',result['text'])
    def test_kernel_signatures_examples_and_release(self):
        for name in ('KokkosBlas::gemm','KokkosSparse::spmv'):
            hit=self.store.search(name,'documentation',library='kokkos-kernels')[0]
            result=self.store.get(hit['id'],include_subsections=True)
            self.assertIn('template',result['text'])
            self.assertEqual(result['version'],'5.2.2')
            self.assertIn('Example',result['text'])
    def test_external_examples_are_available(self):
        hits=self.store.search('KokkosLapack::geqrf','documentation',library='kokkos-kernels',limit=8)
        included=[]
        for hit in hits:included.extend(self.store.get(hit['id'],include_subsections=True)['included_code'])
        self.assertTrue(included)
        self.assertTrue(all(h['library']=='kokkos-kernels' for h in included))

@unittest.skipUnless((ROOT/'standards-lock.json').exists(),'NWS/JEDI corpus not imported')
class StandardsReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.db=Path(cls.temp.name)/'index.sqlite3'
        build(ROOT/'corpus.json',cls.db);cls.store=Knowledge(cls.db)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_nws_environment_variables(self):
        lock=json.loads((ROOT/'standards-lock.json').read_text())
        revision=lock['nws-hpc-standards']['commit']
        hits=self.store.search('Standard Environment Variables','documentation',library='nws-hpc-standards')
        self.assertTrue(hits)
        self.assertTrue(all(h['version']=='11.0.0' for h in hits))
        section=self.store.get(hits[0]['id'],include_subsections=True)
        self.assertIn('PACKAGEROOT',section['text'])
        self.assertIn(revision,section['provenance']['url'])
    def test_jedi_obsgroup_conventions(self):
        lock=json.loads((ROOT/'standards-lock.json').read_text())
        revision=lock['jedi']['commit']
        hits=self.store.search('ObsGroup','documentation',library='jedi')
        self.assertTrue(hits)
        self.assertTrue(all(h['version'].startswith('snapshot-') for h in hits))
        section=self.store.get(hits[0]['id'],include_subsections=True)
        self.assertIn('ObsGroup',section['text'])
        self.assertIn(revision,section['provenance']['url'])
