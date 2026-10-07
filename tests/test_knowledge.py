import json
import tempfile
import unittest
from pathlib import Path
from knowledge import Knowledge, build, html_sections, code_units

HTML='''<html><title>NUOPC 8.9.1</title><body>
<h1><a name="driver"></a>Generic Component NUOPC_Driver</h1><p>Controls components.</p>
<h2><a name="add"></a>NUOPC_DriverAddComp</h2><p>Register a component.</p>
<h3>Signature</h3><pre>call NUOPC_DriverAddComp(driver, label, rc=rc)</pre>
<h3>Arguments</h3><p>driver and label are required. rc is optional.</p>
<h2>Run Sequence</h2><p>Clock ordering and run sequence.</p></body></html>'''
CODE='''module Cap
 use ESMF
 use NUOPC
 implicit none
contains
 subroutine SetServices(model, rc)
  integer :: rc
  call NUOPC_CompDerive(model, rc=rc)
 contains
  subroutine Inner()
  end subroutine Inner
 end subroutine SetServices
 subroutine Advance(model, rc)
  call ESMF_GridCompGet(model, rc=rc)
 end subroutine Advance
end module Cap
'''

class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        (self.root/'manual.html').write_text(HTML)
        (self.root/'cap.F90').write_text(CODE)
        protos=self.root/'protos';protos.mkdir()
        (protos/'README').write_text('README for demo prototype\n---------------------\n\nA pattern example.\n')
        (protos/'run.config').write_text('ATM_petlist: 0-1\n')
        (protos/'mesh.nc').write_bytes(b'\xcdf\xce binary mesh data')
        self.manifest=self.root/'corpus.json';self.db=self.root/'index.sqlite3'
        self.entries=[{'name':'manual','path':'manual.html','version':'8.9.1','kind':'documentation','url':'https://example.com/manual.html'},
                      {'name':'example','path':'cap.F90','version':'8.9.1','kind':'example'},
                      {'name':'app','path':'cap.F90','version':'8.9.1','kind':'application'},
                      {'name':'protos','path':'protos','version':'8.9.1','kind':'example'}]
        self.manifest.write_text(json.dumps({'sources':self.entries})); build(self.manifest,self.db);self.store=Knowledge(self.db)
    def tearDown(self):self.temp.cleanup()
    def test_whole_api_section_and_anchor(self):
        hit=self.store.search('NUOPC_DriverAddComp','documentation')[0]
        self.assertEqual(hit['title'],'NUOPC_DriverAddComp')
        result=self.store.get(hit['id'],include_subsections=True)
        self.assertIn('call NUOPC_DriverAddComp',result['text'])
        self.assertIn('rc is optional',result['text'])
        self.assertNotIn('Clock ordering',result['text'])
        self.assertTrue(result['url'].endswith('#add'));self.assertTrue(result['complete'])
    def test_fortran_nested_routines_and_parent_context(self):
        hit=self.store.search('SetServices','example')[0];result=self.store.get(hit['id'])
        self.assertEqual(result['title'],'Cap::SetServices')
        self.assertIn('end subroutine SetServices',result['text'])
        self.assertIn('subroutine Inner',result['text'])
        self.assertNotIn('subroutine Advance',result['text'])
        self.assertIn('use NUOPC',result['provenance']['module_context'])
        self.assertIn('subroutine Advance',self.store.get(result['parent'])['text'])
        self.assertEqual(result['start_line'],6)
    def test_pagination_roundtrip(self):
        hit=self.store.search('NUOPC_Driver','documentation')[0]
        full=self.store.get(hit['id'],max_characters=32000,include_subsections=True)['text']
        parts=[];offset=0
        while True:
            result=self.store.get(hit['id'],offset,100,True);parts.append(result['text'])
            if result['next_offset'] is None:break
            offset=result['next_offset']
        self.assertEqual(''.join(parts),full)
    def test_kind_and_version_filters(self):
        for kind in ('documentation','example','application'):
            self.assertTrue(all(hit['kind']==kind for hit in self.store.search('rc',kind)))
        with self.assertRaises(ValueError):self.store.search('rc',version='8.8.0')
        context=self.store.context('SetServices','both')
        self.assertTrue(context['examples']);self.assertTrue(context['application'])
    def test_rebuild_rollback_and_stable_ids(self):
        key=self.store.search('SetServices','example')[0]['id']
        build(self.manifest,self.db);self.assertEqual(self.store.search('SetServices','example')[0]['id'],key)
        self.entries.append({'name':'bad','path':'missing.html','version':'8.9.1','kind':'documentation'})
        self.manifest.write_text(json.dumps({'sources':self.entries}))
        with self.assertRaises(ValueError):build(self.manifest,self.db)
        self.assertEqual(self.store.search('SetServices','example')[0]['id'],key)
    def test_invalid_requests(self):
        for query in ('', 'x'*2001):
            with self.assertRaises(ValueError):self.store.search(query)
        self.assertEqual(self.store.search('uniqueabsent'),[])
        self.store.search('" OR * : ()')
        with self.assertRaises(ValueError):self.store.get('../file')
        with self.assertRaises(ValueError):self.store.context('cap','unknown')
    def test_reject_wrong_version_ingest(self):
        self.entries[0]['version']='8.8.0';self.manifest.write_text(json.dumps({'sources':self.entries}))
        with self.assertRaises(ValueError):build(self.manifest,self.db)
        self.assertTrue(self.store.sources())
    def test_unrecognized_routine_keeps_file(self):
        text='subroutine Unusual()\n! uncommon bare END syntax\nend\n'
        units=code_units(text,'odd.F90','')
        self.assertEqual(units[0]['text'],text)
    def test_extended_whitelist_admits_configs_skips_binaries(self):
        readme=[h for h in self.store.search('demo prototype','example')
                if h['source'].endswith('protos/README')]
        self.assertTrue(readme)
        self.assertIn('Full source file:',readme[0]['title'])
        config=[h for h in self.store.search('ATM_petlist','example')
                if h['source'].endswith('protos/run.config')]
        self.assertTrue(config)
        self.assertEqual(self.store.search('mesh','example'),[])
        from knowledge import LIBRARIES
        self.assertIn('ccpp',LIBRARIES)
    def test_new_libraries_accepted(self):
        from knowledge import LIBRARIES
        self.assertIn('nws-hpc-standards',LIBRARIES);self.assertIn('jedi',LIBRARIES);self.assertIn('ccpp-scm',LIBRARIES)
        (self.root/'std.rst').write_text('Standard Environment Variables\n================================\nPACKAGEROOT is the application root.\n')
        self.entries.append({'name':'nws','path':'std.rst','library':'nws-hpc-standards','version':'11.0.0','kind':'documentation'})
        self.manifest.write_text(json.dumps({'sources':self.entries}));build(self.manifest,self.db)
        hits=self.store.search('PACKAGEROOT','documentation',library='nws-hpc-standards')
        self.assertTrue(hits);self.assertEqual(hits[0]['version'],'11.0.0')
        with self.assertRaises(ValueError):self.store.search('x',library='bogus')

if __name__=='__main__':unittest.main()
