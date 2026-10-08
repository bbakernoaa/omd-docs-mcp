"""Fetch the pinned PyTorch and PyTorch Forecasting HTML documentation."""
import argparse
import concurrent.futures
import json
import shutil
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
SITES = {
    'pytorch': {
        'version': '2.14',
        'base_url': 'https://docs.pytorch.org/docs/2.14/',
        'start_pages': ('index.html',),
        'path': 'corpus/pytorch/source',
    },
    'pytorch-forecasting': {
        'version': '1.0.0',
        'base_url': 'https://pytorch-forecasting.readthedocs.io/en/v1.0.0/',
        'start_pages': ('index.html',),
        'path': 'corpus/pytorch-forecasting/source',
    },
}
MAX_PAGES = 10000
MAX_PAGE_BYTES = 30_000_000


def relative_html_path(url, base_url):
    """Return a safe local path for an HTML URL inside one pinned site."""
    base = urllib.parse.urlsplit(base_url)
    parsed = urllib.parse.urlsplit(urllib.parse.urldefrag(url).url)
    base_path = urllib.parse.unquote(base.path)
    page_path = urllib.parse.unquote(parsed.path)
    if (parsed.scheme, parsed.netloc) != (base.scheme, base.netloc):
        raise ValueError(f'URL is outside the pinned documentation host: {url}')
    if not base_path.endswith('/'):
        base_path += '/'
    if not page_path.startswith(base_path):
        raise ValueError(f'URL is outside the pinned documentation path: {url}')
    relative = page_path[len(base_path):]
    if not relative:
        relative = 'index.html'
    elif relative.endswith('/'):
        relative += 'index.html'
    path = PurePosixPath(relative)
    if path.is_absolute() or '..' in path.parts or path.suffix.lower() not in ('.html', '.htm'):
        raise ValueError(f'URL is not a safe HTML page: {url}')
    return path.as_posix()


def links_in_scope(html, page_url, base_url):
    """Find canonical, same-release HTML links in one page."""
    links = set()
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup.find_all('a', href=True):
        url = urllib.parse.urldefrag(urllib.parse.urljoin(page_url, tag['href'])).url
        try:
            relative_html_path(url, base_url)
        except ValueError:
            continue
        parsed = urllib.parse.urlsplit(url)
        base = urllib.parse.urlsplit(base_url)
        path = urllib.parse.unquote(parsed.path)
        base_path = urllib.parse.unquote(base.path)
        if path.endswith('/'):
            path += 'index.html'
        links.add(urllib.parse.urlunsplit((base.scheme, base.netloc,
                                           urllib.parse.quote(path, safe='/:@'), '', '')))
    return links


def fetch_html(url, base_url):
    request = urllib.request.Request(url, headers={'User-Agent': 'omd-docs-mcp/1.0'})
    with urllib.request.urlopen(request, timeout=40) as response:
        final_url = urllib.parse.urldefrag(response.url).url
        relative_html_path(final_url, base_url)
        content_type = response.headers.get_content_type()
        if content_type not in ('text/html', 'application/xhtml+xml'):
            raise ValueError(f'Expected HTML at {url}; received {content_type}')
        data = response.read(MAX_PAGE_BYTES + 1)
    if len(data) > MAX_PAGE_BYTES:
        raise ValueError(f'HTML page too large: {url}')
    return data.decode('utf-8'), final_url


def crawl_site(library, output):
    config = SITES[library]
    base_url = config['base_url']
    pending = {urllib.parse.urljoin(base_url, page) for page in config['start_pages']}
    visited = set()
    stored = set()
    reported = 0
    while pending:
        if len(visited) + len(pending) > MAX_PAGES:
            raise ValueError(f'{library}: exceeded the {MAX_PAGES}-page crawl limit')
        batch = sorted(pending - visited)
        pending.clear()
        if not batch:
            break
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            fetched = list(pool.map(lambda url: (url, fetch_html(url, base_url)), batch))
        for url, (html, final_url) in fetched:
            relative = relative_html_path(final_url, base_url)
            destination = output / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(html, encoding='utf-8')
            stored.add(relative)
            visited.add(url)
            visited.add(final_url)
            pending.update(links_in_scope(html, final_url, base_url) - visited)
        if len(stored) >= reported + 100:
            reported = len(stored)
            print(f'{library}: fetched {reported} HTML pages', flush=True)
    if not visited:
        raise ValueError(f'{library}: no pages were fetched')
    return len(stored)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=ROOT / 'corpus.catalog.json')
    args = parser.parse_args()
    catalog_path = args.catalog
    catalog = json.loads(catalog_path.read_text())
    sources = catalog.get('sources', [])
    for library in SITES:
        if any(entry.get('library') == library and not entry.get('managed') for entry in sources):
            parser.error(f'{library} has custom source entries; preserve them before refreshing')
    with tempfile.TemporaryDirectory(prefix='pytorch-fetch-', dir=ROOT) as temp:
        stage = Path(temp)
        counts = {}
        for library in SITES:
            counts[library] = crawl_site(library, stage / library / 'source')
        for library, config in SITES.items():
            destination = ROOT / config['path']
            if destination.exists():
                shutil.rmtree(destination)
            shutil.move(str(stage / library / 'source'), str(destination))
        sources = [entry for entry in sources if entry.get('library') not in SITES]
        for library, config in SITES.items():
            sources.append({
                'name': library + '-docs',
                'path': config['path'],
                'library': library,
                'version': config['version'],
                'kind': 'documentation',
                'managed': True,
                'url': config['base_url'],
                'version_basis': 'Official versioned documentation site; pages restricted to the pinned release path',
            })
        catalog_path.write_text(json.dumps({'sources': sources}, indent=2) + '\n')
    for library, count in counts.items():
        print(f'{library}: fetched {count} HTML pages', flush=True)
    print('PyTorch documentation fetched. Run ingest.py to rebuild the index.', flush=True)


if __name__ == '__main__':
    main()