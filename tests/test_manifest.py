import json
import tempfile
import unittest
from pathlib import Path

from build_manifest import generate


class ManifestBuildTests(unittest.TestCase):
    def test_generates_corpus_json_from_catalog(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / 'corpus.catalog.json'
            output = root / 'corpus.json'
            (root / 'manual.html').write_text('<h1>Manual</h1>')
            sources = [{'name': 'manual', 'path': 'manual.html', 'library': 'esmf',
                        'version': '8.9.1', 'kind': 'documentation'},
                       {'name': 'pytorch-docs', 'path': 'corpus/pytorch/source',
                        'library': 'pytorch', 'version': '2.14', 'kind': 'documentation'}]
            catalog.write_text(json.dumps({'sources': sources}))

            self.assertEqual(generate(catalog, output), 1)
            self.assertEqual(json.loads(output.read_text()), {'sources': sources[:1]})

    def test_rejects_an_empty_catalog_without_overwriting_existing_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / 'corpus.catalog.json'
            output = root / 'corpus.json'
            catalog.write_text('{"sources": []}')
            output.write_text('previous manifest')

            with self.assertRaises(ValueError):
                generate(catalog, output)

            self.assertEqual(output.read_text(), 'previous manifest')


if __name__ == '__main__':
    unittest.main()