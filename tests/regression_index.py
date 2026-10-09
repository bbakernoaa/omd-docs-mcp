"""Shared full-corpus index for release regression tests.

The ESMF, Kokkos, standards and CCPP regression suites all query the same
committed corpus, so the index is built once per test process and reused.
The large fetched PyTorch collections are excluded: they are covered by
their own focused tests and add minutes of HTML parsing to every rebuild.
"""
import json
import tempfile
from pathlib import Path

from build_manifest import FETCHED_LIBRARIES, generate
from knowledge import Knowledge, build

ROOT = Path(__file__).resolve().parents[1]

_cache = {}


def _manifest(temp_dir):
    """Regression manifest with absolute source paths, so it can live in a
    temporary directory instead of overwriting the workspace manifest."""
    catalog = ROOT / 'corpus.catalog.json'
    raw = temp_dir / 'corpus.json'
    generate(catalog, raw, exclude=FETCHED_LIBRARIES)
    manifest = json.loads(raw.read_text())
    for entry in manifest['sources']:
        entry['path'] = str((catalog.parent / entry['path']).resolve())
    manifest_path = temp_dir / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest))
    return manifest_path


def _ensure():
    if 'store' not in _cache:
        temp = tempfile.TemporaryDirectory()
        directory = Path(temp.name)
        database = directory / 'index.sqlite3'
        build(_manifest(directory), database)
        _cache['temp'] = temp
        _cache['database'] = database
        _cache['store'] = Knowledge(database)
    return _cache


def regression_store():
    return _ensure()['store']


def regression_database():
    return _ensure()['database']
