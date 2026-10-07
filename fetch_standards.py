"""Import NWS-HPC standards, JEDI and CCPP documentation, preserving other corpus collections."""
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
    'nws-hpc-standards': {'repo':'NCO-HPC/nws-hpc-standards','ref':'v11.0.0',
        'commit':'d0e8f079b66891d39fe7494a1c68bd7c77639425','version':'11.0.0','doc_dir':'docs',
        'exts':['.rst','.md'],'license':'disclaimer',
        'rtd_url':'https://nws-hpc-standards.readthedocs.io/en/stable/'},
    'jedi': {'repo':'JCSDA/jedi-docs','ref':'7cd222915252711893bf341bc1b67ffef3b2824a','branch':'develop',
        'commit':'7cd222915252711893bf341bc1b67ffef3b2824a','version':'snapshot-7cd222915252',
        'doc_release':'8.0.0','doc_dir':'docs','exts':['.rst','.md'],'conf_path':'docs/conf.py','license':'required',
        'rtd_url':'https://jcsda-jedi-docs.readthedocs-hosted.com/en/latest/'},
    'ccpp': {'repo':'NCAR/ccpp-doc','ref':'a2f65334fda991fb7aa6a37716c003533529370e','branch':'main',
        'commit':'a2f65334fda991fb7aa6a37716c003533529370e','version':'snapshot-a2f65334fda9',
        'doc_release':'6.0.0','doc_dir':'CCPPtechnical/source','exts':['.rst','.inc','.txt'],
        'conf_path':'CCPPtechnical/source/conf.py','license':'none',
        'skip_dirs':['_static','_templates','.git','__pycache__','_build','venv'],
        'included_code':['_static/scheme_template.F90','_static/scheme_template.meta'],
        'rtd_url':'https://ccpp-doc.readthedocs.io/en/latest/'},
    'ccpp-scm': {'repo':'NCAR/ccpp-scm','ref':'a52680b013066e0f3135d63ae587ced18a434e86','branch':'main',
        'commit':'a52680b013066e0f3135d63ae587ced18a434e86','version':'snapshot-a52680b01306',
        'doc_release':'7.0.1','doc_dir':'scm/doc/TechGuide','exts':['.rst','.txt'],
        'conf_path':'scm/doc/TechGuide/conf.py','license':'required',
        'skip_dirs':['_static','_templates','.git','__pycache__','_build','venv','images'],
        'included_code':['dephy_case_header.txt','css_nml.txt','css_nml_ex2.txt'],
        'rtd_url':'https://ccpp-scm.readthedocs.io/en/latest/'},
}

def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()

def latest_release(repo):
    req=urllib.request.Request(f'https://api.github.com/repos/{repo}/releases/latest',headers={'User-Agent':'omd-context/1.0'})
    with urllib.request.urlopen(req,timeout=30) as response:result=json.load(response)
    if result.get('draft') or result.get('prerelease'):raise ValueError('Expected latest stable release')
    return result['tag_name']

def copy_markdown(source_dir,target_dir,exts=('.rst','.md'),skip_dirs=('_build','venv','.git','__pycache__')):
    """Copy matching-extension files, preserving the relative tree; skip build/asset directories."""
    copied=0
    for path in sorted(source_dir.rglob('*')):
        if not path.is_file() or path.suffix.lower() not in exts:continue
        relative=path.relative_to(source_dir)
        if any(part in skip_dirs for part in relative.parts):continue
        destination=target_dir/relative
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,destination);copied+=1
    return copied

def read_license(repo,marker):
    """Return the markdown section whose heading matches `marker`, for provenance."""
    for name in ('README.md','README.rst'):
        file=repo/name
        if not file.is_file():continue
        lines=file.read_text(encoding='utf-8',errors='replace').splitlines(keepends=True)
        start=None;level=0
        for index,line in enumerate(lines):
            match=re.match(r'^(#+)\s*'+re.escape(marker)+r'\s*$',line,re.I)
            if match:start=index;level=len(match.group(1));break
        if start is None:return ''.join(lines)
        end=len(lines)
        for index in range(start+1,len(lines)):
            match=re.match(r'^(#+)\s',lines[index])
            if match and len(match.group(1))<=level:end=index;break
        return ''.join(lines[start:end]).rstrip()+'\n'
    return ''

def read_doc_release(repo,fallback,conf_path='docs/conf.py'):
    """Read the Sphinx release from the checked-out conf.py at conf_path; fall back if absent."""
    conf=repo/conf_path
    if conf.is_file():
        match=re.search(r"^release\s*=\s*['\"]([^'\"]+)['\"]",conf.read_text(encoding='utf-8',errors='replace'),re.M)
        if match:return match.group(1)
    return fallback

def commit_tag_version(repo,ref):
    """For NWS, derive the numeric version from the tag (strip leading v)."""
    tag=ref.split('/')[-1]
    return re.sub(r'^v','',tag)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nws-repo',type=Path,help='Use a local NWS-HPC standards checkout')
    parser.add_argument('--jedi-repo',type=Path,help='Use a local JEDI docs checkout')
    parser.add_argument('--ccpp-repo',type=Path,help='Use a local CCPP docs checkout')
    parser.add_argument('--ccpp-scm-repo',type=Path,help='Use a local CCPP-SCM docs checkout')
    parser.add_argument('--latest',action='store_true',help='Refresh to the newest NWS release tag, current JEDI develop, and current CCPP/CCPP-SCM main; record new commits')
    args=parser.parse_args()
    manifest=ROOT/'corpus.json'
    prior=json.loads(manifest.read_text()) if manifest.exists() else {'sources':[]}
    for entry in prior['sources']:
        if entry.get('library') in DEFAULT and not entry.get('managed'):
            raise ValueError('Custom NWS/JEDI source entries exist; preserve them separately before refresh')
    sources=[entry for entry in prior['sources'] if entry.get('library') not in DEFAULT]
    lock={}
    with tempfile.TemporaryDirectory(prefix='standards-fetch-',dir=ROOT) as tmp:
        stage=Path(tmp)
        for library,config in DEFAULT.items():
            config=dict(config)
            supplied={'nws-hpc-standards':args.nws_repo,'jedi':args.jedi_repo,'ccpp':args.ccpp_repo,'ccpp-scm':args.ccpp_scm_repo}[library]
            repo=supplied.resolve() if supplied else stage/(library+'-repo')
            ref=config['ref']
            if args.latest:
                ref=latest_release(config['repo']) if library=='nws-hpc-standards' else config['branch']
            if not supplied:
                subprocess.run(['git','init',str(repo)],check=True,stdout=subprocess.DEVNULL)
                subprocess.run(['git','-C',str(repo),'remote','add','origin','https://github.com/'+config['repo']+'.git'],check=True)
                subprocess.run(['git','-C',str(repo),'fetch','--depth','1','origin',ref],check=True)
                subprocess.run(['git','-C',str(repo),'checkout','--detach','FETCH_HEAD'],check=True)
            commit=git(repo,'rev-parse','HEAD')
            if not args.latest and commit!=config['commit']:raise ValueError(f'{library}: checkout does not match pinned commit')
            if git(repo,'status','--porcelain'):raise ValueError(f'{library}: checkout is modified')
            if 'conf_path' in config:config['doc_release']=read_doc_release(repo,config.get('doc_release',''),config['conf_path'])
            if args.latest:
                if library=='nws-hpc-standards':config['version']=commit_tag_version(repo,ref)
                else:config['version']='snapshot-'+commit[:12]
                config['commit']=commit;config['ref']=ref
            if args.latest and supplied:
                remote=git(repo,'ls-remote','origin',ref,ref+'^{}','refs/heads/'+ref,'refs/tags/'+ref,'refs/tags/'+ref+'^{}')
                commits=[line.split()[0] for line in remote.splitlines()]
                if commit not in commits:raise ValueError(f'{library}: supplied checkout is not the requested latest ref')
            target=stage/library
            source=repo/config['doc_dir']
            if not source.is_dir():raise ValueError(f'{library}: docs directory {config["doc_dir"]} missing')
            count=copy_markdown(source,target/'source',exts=tuple(config['exts']),skip_dirs=tuple(config.get('skip_dirs',('_build','venv','.git','__pycache__'))))
            if count==0:raise ValueError(f'{library}: no documentation files found')
            if config['license']=='required':
                for name in ('COPYING','LICENSE'):
                    file=repo/name
                    if file.is_file():shutil.copy2(file,target/name);break
                else:raise ValueError(f'{library}: no COPYING or LICENSE file found')
            elif config['license']=='disclaimer':
                disclaimer=read_license(repo,'Disclaimer')
                (target/'DISCLAIMER.md').write_text(disclaimer or 'No license file; see upstream repository disclaimer.\n')
            included_files=[]
            for reference in config.get('included_code',[]):
                file=source/reference
                if not file.is_file():raise ValueError(f'{library}: literalinclude target missing: {reference}')
                destination=target/'included-code'/reference
                destination.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(file,destination);included_files.append(destination)
            if library=='nws-hpc-standards':
                basis='Official release tag '+ref+'; matches RTD /en/stable/'
            elif library=='jedi':
                basis='Rolling develop snapshot matching RTD /en/latest/; docs/conf.py declares release '+config.get('doc_release','')+'; not release-certified'
            elif library=='ccpp':
                basis=('Rolling main snapshot matching RTD /en/latest/; conf.py declares release '
                       +config.get('doc_release','')+'; not release-certified; repository has no license file')
            else:
                basis=('Rolling main snapshot matching RTD /en/latest/; conf.py declares release '
                       +config.get('doc_release','')+'; not release-certified')
            entry={'name':library+'-docs','path':f'corpus/{library}/source','library':library,
                'version':config['version'],'kind':'documentation','managed':True,'revision':commit,
                'url':f'https://github.com/{config["repo"]}/blob/{commit}/{config["doc_dir"]}','version_basis':basis}
            if 'doc_release' in config:entry['target_release']=config.get('doc_release')
            sources.append(entry)
            if included_files:
                sources.append({'name':library+'-included-code','path':f'corpus/{library}/included-code','library':library,
                    'version':config['version'],'kind':'example','managed':True,'revision':commit,
                    'url':f'https://github.com/{config["repo"]}/blob/{commit}/{config["doc_dir"]}','version_basis':'Files referenced by documentation literalinclude directives'})
            lock[library]={**config,'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        # No live corpus changes occur until every checkout has been verified and copied.
        for library in DEFAULT:
            destination=ROOT/'corpus'/library
            if destination.exists():shutil.rmtree(destination)
            shutil.move(str(stage/library),str(destination))
        manifest.write_text(json.dumps({'sources':sources},indent=2)+'\n')
        (ROOT/'standards-lock.json').write_text(json.dumps(lock,indent=2)+'\n')
    print('NWS-HPC standards, JEDI, CCPP and CCPP-SCM documentation imported. Run uv run ingest.py')

if __name__=='__main__':main()