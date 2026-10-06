"""Import official Kokkos documentation, preserving other corpus collections."""
import argparse
import datetime
import json
import re
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DEFAULT={
    'kokkos': {'repo':'kokkos/kokkos-core-wiki','commit':'3cf2e0638b2419f4631fa85ea2b9aca47004dc18',
               'version':'snapshot-3cf2e0638b24','target_release':'5.2.2'},
    'kokkos-kernels': {'repo':'kokkos/kokkos-kernels','commit':'30ad8eddc07f98f73ad22d5ed59cbea78277b03e',
                       'version':'5.2.2','tag':'5.2.2'}
}

def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()

def latest_release(repo):
    req=urllib.request.Request(f'https://api.github.com/repos/{repo}/releases/latest',headers={'User-Agent':'hpc-docs-mcp/1.1'})
    with urllib.request.urlopen(req,timeout=30) as response:result=json.load(response)
    if result.get('draft') or result.get('prerelease'):raise ValueError('Expected latest stable release')
    return result['tag_name']

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core-repo',type=Path,help='Use a local official docs checkout')
    parser.add_argument('--kernels-repo',type=Path,help='Use a local official Kernels checkout')
    parser.add_argument('--latest',action='store_true',help='Explicitly refresh core docs HEAD and latest stable Kernels release; record new commits')
    args=parser.parse_args()
    manifest=ROOT/'corpus.json'
    prior=json.loads(manifest.read_text()) if manifest.exists() else {'sources':[]}
    for entry in prior['sources']:
        if entry.get('library') in DEFAULT and not entry.get('managed'):
            raise ValueError('Custom Kokkos source entries exist; preserve them separately before refresh')
    sources=[entry for entry in prior['sources'] if entry.get('library') not in DEFAULT]
    lock={}
    with tempfile.TemporaryDirectory(prefix='kokkos-fetch-',dir=ROOT) as tmp:
        stage=Path(tmp)
        for library,config in DEFAULT.items():
            config=dict(config)
            supplied=args.core_repo if library=='kokkos' else args.kernels_repo
            repo=supplied.resolve() if supplied else stage/(library+'-repo')
            ref=config['commit']
            if args.latest:
                if library=='kokkos':
                    ref='main';config['target_release']=latest_release('kokkos/kokkos')
                else:
                    ref=latest_release('kokkos/kokkos-kernels');config['tag']=ref;config['version']=ref
            if not supplied:
                subprocess.run(['git','init',str(repo)],check=True,stdout=subprocess.DEVNULL)
                subprocess.run(['git','-C',str(repo),'remote','add','origin','https://github.com/'+config['repo']+'.git'],check=True)
                subprocess.run(['git','-C',str(repo),'fetch','--depth','1','origin',ref],check=True)
                subprocess.run(['git','-C',str(repo),'checkout','--detach','FETCH_HEAD'],check=True)
            commit=git(repo,'rev-parse','HEAD')
            if not args.latest and commit!=config['commit']:raise ValueError(f'{library}: checkout does not match pinned commit')
            if git(repo,'status','--porcelain'):raise ValueError(f'{library}: checkout is modified')
            if args.latest and library=='kokkos':config['version']='snapshot-'+commit[:12]
            if args.latest and supplied:
                remote=git(repo,'ls-remote','origin',ref,ref+'^{}','refs/heads/'+ref,'refs/tags/'+ref,'refs/tags/'+ref+'^{}')
                commits=[line.split()[0] for line in remote.splitlines()]
                if commit not in commits:raise ValueError(f'{library}: supplied checkout is not the requested latest ref')
            source=repo/'docs'/'source'
            if not source.is_dir():raise ValueError('Official docs/source directory missing')
            target=stage/library
            shutil.copytree(source,target/'source')
            for path in repo.iterdir():
                if path.is_file() and any(word in path.name.lower() for word in ('license','copyright')):
                    shutil.copy2(path,target/path.name)
            basis='Official rolling core documentation snapshot; not release-certified' if library=='kokkos' else 'Official documentation from verified release commit'
            sources.append({'name':library+'-docs','path':f'corpus/{library}/source','library':library,
                'version':config['version'],'kind':'documentation','managed':True,'revision':commit,
                'url':f'https://github.com/{config["repo"]}/blob/{commit}/docs/source',
                'version_basis':basis,'target_release':config.get('target_release',config['version'])})
            if library=='kokkos-kernels':
                referenced=set()
                missing=[]
                for page in source.rglob('*.rst'):
                    for ref in re.findall(r'^\s*\.\. literalinclude::\s*(.+)$',page.read_text(),re.M):
                        file=(page.parent/ref.strip()).resolve()
                        if file.is_file() and file.is_relative_to(repo):referenced.add(file)
                        else:missing.append(ref.strip())
                for file in referenced:
                    destination=target/'included-code'/file.relative_to(repo)
                    destination.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copy2(file,destination)
                if referenced:sources.append({'name':'kokkos-kernels-includes','path':'corpus/kokkos-kernels/included-code',
                    'library':library,'version':config['version'],'kind':'example','managed':True,'revision':commit,
                    'url':f'https://github.com/{config["repo"]}/blob/{commit}',
                    'version_basis':'Example files referenced by release documentation','missing_includes':missing})
            lock[library]={**config,'commit':commit,'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        # No live corpus changes occur until both checkouts have been verified and copied.
        for library in DEFAULT:
            destination=ROOT/'corpus'/library
            if destination.exists():shutil.rmtree(destination)
            shutil.move(str(stage/library),str(destination))
        manifest.write_text(json.dumps({'sources':sources},indent=2)+'\n')
        (ROOT/'kokkos-lock.json').write_text(json.dumps(lock,indent=2)+'\n')
    print('Kokkos documentation imported. Run uv run ingest.py')

if __name__=='__main__':main()
