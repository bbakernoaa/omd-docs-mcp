"""Generate the runtime ingestion manifest from the committed source catalog."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FETCHED_LIBRARIES = {'pytorch', 'pytorch-forecasting'}


def generate(catalog_path, output_path, exclude=frozenset()):
    catalog_path = Path(catalog_path)
    output_path = Path(output_path)
    manifest = json.loads(catalog_path.read_text())
    sources = [
        entry for entry in manifest.get('sources', [])
        if entry.get('library') not in exclude
        and (entry.get('library') not in FETCHED_LIBRARIES
             or (catalog_path.parent / entry['path']).exists())
    ]
    if not sources:
        raise ValueError('Catalog has no sources; existing manifest preserved')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({'sources': sources}, indent=2) + '\n')
    return len(sources)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=ROOT / 'corpus.catalog.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'corpus.json')
    args = parser.parse_args()
    try:
        count = generate(args.catalog, args.output)
    except Exception as error:
        parser.exit(1, f'Manifest generation failed; prior manifest preserved: {error}\n')
    print(f'Generated {args.output} with {count} source entries')


if __name__ == '__main__':
    main()