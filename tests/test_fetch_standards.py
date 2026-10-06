import json
import subprocess
import tempfile
import unittest
from pathlib import Path
import fetch_standards

ROOT=Path(__file__).resolve().parents[1]

class FetchStandardsHelpers(unittest.TestCase):
    def test_copy_markdown_filters_and_skips_venv(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/'docs';dst=Path(tmp)/'out'
            (src/'sub').mkdir(parents=True);(src/'venv').mkdir()
            (src/'a.rst').write_text('A\n=\n')
            (src/'b.md').write_text('# B\n')
            (src/'conf.py').write_text('x=1\n')
            (src/'venv'/'c.rst').write_text('C\n=\n')
            (src/'sub'/'d.rst').write_text('D\n=\n')
            n=fetch_standards.copy_markdown(src,dst)
            self.assertEqual(n,3)
            self.assertTrue((dst/'a.rst').is_file() and (dst/'b.md').is_file() and (dst/'sub'/'d.rst').is_file())
            self.assertFalse((dst/'conf.py').exists() or (dst/'venv'/'c.rst').exists())
    def test_copy_docs_honours_extensions_and_skip_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/'CCPPtechnical'/'source';dst=Path(tmp)/'out'
            (src/'_static').mkdir(parents=True)
            (src/'a.rst').write_text('A\n=\n')
            (src/'prolog.inc').write_text('.. |c| replace:: CCPP\n')
            (src/'ccpp_physics.txt').write_text('physics tree\n')
            (src/'conf.py').write_text("release='9'\n")
            (src/'references.bib').write_text('@misc{x}\n')
            (src/'_static'/'fig.png').write_bytes(b'\x89PNG')
            n=fetch_standards.copy_markdown(src,dst,exts=('.rst','.inc','.txt'),skip_dirs=('_static','_templates','.git','__pycache__','_build','venv'))
            self.assertEqual(n,3)
            self.assertTrue((dst/'prolog.inc').is_file() and (dst/'ccpp_physics.txt').is_file())
            self.assertFalse((dst/'conf.py').exists() or (dst/'references.bib').exists() or (dst/'_static').exists())
    def test_commit_tag_version_strips_v(self):
        self.assertEqual(fetch_standards.commit_tag_version(None,'v11.0.0'),'11.0.0')
        self.assertEqual(fetch_standards.commit_tag_version(None,'refs/tags/v11.0.0'),'11.0.0')
    def test_read_doc_release_prefers_conf_py(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=Path(tmp)
            (repo/'docs').mkdir();(repo/'docs'/'conf.py').write_text("version = '9'\nrelease = '9.1.0'\n")
            self.assertEqual(fetch_standards.read_doc_release(repo,'8.0.0'),'9.1.0')
            (repo/'docs'/'conf.py').write_text("no release here\n")
            self.assertEqual(fetch_standards.read_doc_release(repo,'8.0.0'),'8.0.0')
    def test_read_doc_release_uses_conf_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=Path(tmp)
            conf=repo/'CCPPtechnical'/'source'/'conf.py';conf.parent.mkdir(parents=True)
            conf.write_text("version = '6.0'\nrelease = '6.0.0'\n")
            self.assertEqual(fetch_standards.read_doc_release(repo,'fallback',conf_path='CCPPtechnical/source/conf.py'),'6.0.0')
            self.assertEqual(fetch_standards.read_doc_release(repo,'fallback',conf_path='nope/conf.py'),'fallback')

if __name__=='__main__':unittest.main()