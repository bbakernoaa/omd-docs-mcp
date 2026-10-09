"""Fetch pinned official manuals and release code; never runs from an MCP tool."""
import argparse
import concurrent.futures
import json
import shutil
import subprocess
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent
COMMIT='bd03a249df907464fdad91b7c43985dedbc472c7'
BASE='https://earthsystemmodeling.org/docs/release/ESMF_8_9_1/'
MANUALS=('NUOPC_refdoc','NUOPC_howtodoc','ESMF_refdoc','ESMC_crefdoc')
PROTOS_REPO='https://github.com/esmf-org/nuopc-app-prototypes.git'
PROTOS_REF='patch/8.9.1'
PROTOS_COMMIT='1645f4471da271e518213ceb574b0ada0ff3a169'


def download(url):
    request=urllib.request.Request(url,headers={'User-Agent':'omd-context/1.0'})
    with urllib.request.urlopen(request,timeout=40) as response:
        if not response.url.startswith(BASE):raise ValueError('Manual redirected outside pinned release')
        data=response.read(30_000_001)
    if len(data)>30_000_000:raise ValueError('Manual page too large')
    text=data.decode('utf-8')
    if '<html' not in text.lower() or '<title' not in text.lower():raise ValueError('Not an HTML manual')
    return text


def fetch_manual(name,target):
    base=BASE+name+'/'
    index=download(base)
    soup=BeautifulSoup(index,'html.parser')
    if '8.9.1' not in soup.get_text(' ',strip=True):raise ValueError(f'{name}: release version not found')
    urls=set()
    for tag in soup.find_all('a',href=True):
        url=urllib.parse.urljoin(base,tag['href']).split('#')[0]
        if url.startswith(base) and Path(urllib.parse.urlsplit(url).path).name.startswith('node') and url.endswith('.html'):
            urls.add(url)
    if not urls or len(urls)>500:raise ValueError('Unexpected manual link inventory')
    target.mkdir(parents=True,exist_ok=True)
    def save(url):
        text=download(url)
        path=target/Path(urllib.parse.urlsplit(url).path).name
        path.write_text(text)
        return path.name
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for future in concurrent.futures.as_completed([pool.submit(save,url) for url in sorted(urls)]):future.result()
    print(f'{name}: fetched {len(urls)} HTML pages',flush=True)


def run(command):return subprocess.check_output(command,text=True).strip()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--esmf-repo',type=Path,help='Existing clean checkout at the pinned v8.9.1 commit')
    parser.add_argument('--skip-manuals',action='store_true',help='Reuse already downloaded corpus/manuals')
    parser.add_argument('--protos-repo',type=Path,help='Existing clean checkout at the pinned prototypes patch/8.9.1 commit')
    args=parser.parse_args()
    manifest_path=ROOT/'corpus.catalog.json'
    if manifest_path.exists():
        prior=json.loads(manifest_path.read_text())
        if any(not entry.get('managed') for entry in prior.get('sources',[]) if entry.get('library','esmf')=='esmf'):
            parser.error('Manifest has custom sources. Save them separately before refreshing official corpus; they will not be overwritten.')
    with tempfile.TemporaryDirectory(prefix='nuopc-fetch-',dir=ROOT) as tmp:
        staging=Path(tmp)
        if args.skip_manuals:
            for name in MANUALS:
                existing=ROOT/'corpus'/'manuals'/name
                if not existing.is_dir():raise ValueError(f'Missing cached manual {name}')
                shutil.copytree(existing,staging/'manuals'/name)
        else:
            for name in MANUALS:fetch_manual(name,staging/'manuals'/name)
        repo=args.esmf_repo.resolve() if args.esmf_repo else staging/'esmf'
        if not args.esmf_repo:
            subprocess.run(['git','clone','--depth','1','--branch','v8.9.1','--filter=blob:none','--sparse',
                            'https://github.com/esmf-org/esmf.git',str(repo)],check=True)
            subprocess.run(['git','-C',str(repo),'sparse-checkout','set','src/addon/NUOPC'],check=True)
        if run(['git','-C',str(repo),'rev-parse','HEAD'])!=COMMIT:raise ValueError('Source checkout does not match pinned ESMF 8.9.1 commit')
        if run(['git','-C',str(repo),'status','--porcelain']):raise ValueError('Source checkout has modifications; refusing to call it a release snapshot')
        for name in ('examples','src'):
            path=repo/'src'/'addon'/'NUOPC'/name
            if not path.is_dir():raise ValueError(f'Missing NUOPC {name} directory')
            shutil.copytree(path,staging/name)
        license_files=[p for p in repo.iterdir() if p.is_file() and ('license' in p.name.lower() or p.name.lower()=='readme')]
        for path in license_files:shutil.copy2(path,staging/path.name)
        protos=args.protos_repo.resolve() if args.protos_repo else staging/'protos-repo'
        if not args.protos_repo:
            subprocess.run(['git','clone','--depth','1','--branch',PROTOS_REF,PROTOS_REPO,str(protos)],check=True)
        if run(['git','-C',str(protos),'rev-parse','HEAD'])!=PROTOS_COMMIT:raise ValueError('Prototypes checkout does not match pinned patch/8.9.1 commit')
        if run(['git','-C',str(protos),'status','--porcelain']):raise ValueError('Prototypes checkout has modifications; refusing to snapshot it')
        shutil.copytree(protos,staging/'nuopc-app-prototypes',ignore=shutil.ignore_patterns('.git'))
        if not any((staging/'nuopc-app-prototypes').rglob('*.F90')):raise ValueError('Prototypes tree contains no Fortran sources')
        target=ROOT/'corpus';target.mkdir(exist_ok=True)
        for name in ('manuals','examples','src','nuopc-app-prototypes'):
            destination=target/name
            if destination.exists():shutil.rmtree(destination)
            shutil.move(str(staging/name),str(destination))
        for path in license_files:shutil.copy2(staging/path.name,target/path.name)
        sources=[entry for entry in (prior.get('sources',[]) if manifest_path.exists() else []) if entry.get('library','esmf')!='esmf']
        for name in MANUALS:
            sources.append({'name':name,'path':f'corpus/manuals/{name}','version':'8.9.1',
                'kind':'documentation','url':BASE+name+'/', 'managed':True,
                'version_basis':'Official 8.9.1 release URL and release label checked on manual index'})
        for name,kind in [('examples','example'),('src','implementation')]:
            sources.append({'name':f'esmf/NUOPC/{name}','path':f'corpus/{name}','version':'8.9.1','kind':kind,
                'url':f'https://github.com/esmf-org/esmf/blob/{COMMIT}/src/addon/NUOPC/{name}',
                'revision':COMMIT,'managed':True,'version_basis':'Clean release checkout verified by commit'})
        sources.append({'name':'nuopc-app-prototypes','path':'corpus/nuopc-app-prototypes','version':'8.9.1',
            'kind':'example','url':f'https://github.com/esmf-org/nuopc-app-prototypes/blob/{PROTOS_COMMIT}',
            'revision':PROTOS_COMMIT,'managed':True,
            'version_basis':'patch/8.9.1 branch tip verified by commit; no 8.9.1 tag exists upstream; repository has no license file (sources carry the Illinois-NCSA header)'})
        manifest_path.write_text(json.dumps({'sources':sources},indent=2)+'\n')
        print('Pinned corpus ready. Run uv run ingest.py',flush=True)

if __name__=='__main__':main()
