# NUOPC Application Prototypes + CCPP Technical Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fold the 51 NUOPC application prototypes into the `esmf/8.9.1` collection as a fourth managed `kind='example'` source, and add `NCAR/ccpp-doc` as a new sixth library `ccpp` (rolling `main` snapshot) with an `get_ccpp_context` tool.

**Architecture:** Two parallel tracks share one ingest-whitelist change. Prototypes reuse the existing esmf machinery (`fetch_corpus.py` + `corpus/nuopc-app-prototypes/`); CCPP generalises `fetch_standards.py` from a hardcoded NWS/JEDI shape into per-library config (`doc_dir`, `exts`, `skip_dirs`, `conf_path`, `license`, `included_code`) and adds `ccpp` to `LIBRARIES` with a docs + included-code entry pair that the existing `literalinclude` resolver consumes. One final task reindexes, tests, documents, rebuilds and pushes.

**Tech Stack:** Python 3.11+ (uv-managed), SQLite FTS5 index, stdlib-only fetchers (subprocess/git), unittest (NO pytest), FastMCP server, Docker.

Spec: `docs/superpowers/specs/2026-10-06-nuopc-app-prototypes-design.md` (commit d3afc39).

## Global Constraints

- ESMF stays restricted to `8.9.1`; `build()` rejects any other esmf version. Prototypes inherit version label `8.9.1` and `kind='example'`.
- CCPP version label is `snapshot-a2f65334fda9` (12-char prefix of commit `a2f65334fda991fb7aa6a37716c003533529370e`); conf.py `release='6.0.0'` is recorded ONLY as informational `target_release`.
- Prototype pin: branch `patch/8.9.1`, commit `1645f4471da271e518213ceb574b0ada0ff3a169`.
- No binary assets indexed: `.nc` and PNG/CSS are never admitted (whitelist is opt-in; `read_text(errors='strict')` would abort on them).
- Ingest whitelist additions are EXACT: suffixes `.c .config .cfg .cmake .sh .runconfig .jl .inc .meta` plus bare name `readme`. Verified zero existing corpus files match, so existing collections must stay byte-identical.
- Baseline per-(library,version,kind) unit counts (from `data/nuopc.sqlite3` today):
  `esmf/8.9.1 documentation 1764, example 18, implementation 356`; `kokkos 1610`; `kokkos-kernels documentation 595, example 46`; `nws-hpc-standards 22`; `jedi 1900`.
  After both additions (measured on a probe index built from the real corpus + both new trees):
  `esmf example 1039` (+1021), `ccpp documentation 137, example 3`, everything else unchanged. esmf total `2138 -> 3159`.
- Test commands: `uv run python -m unittest discover -s tests -t .` (currently 25 tests) and `uv run python tests/smoke_mcp.py`. NEVER `git add -A` — `.superpowers/` is untracked scratch; always use explicit paths.
- Server tool count goes 10 -> 11 (`get_ccpp_context`); `search_docs` docstring and FastMCP instructions mention six libraries.
- Fetchers refuse dirty or wrong-commit checkouts, refuse to clobber unmanaged custom entries, and stage inside a temp dir so failures leave prior corpus/manifest/index intact.

---

### Task 1: Ingest whitelist extension + `ccpp` library label

**Files:**
- Modify: `knowledge.py:10` (LIBRARIES), `knowledge.py:157` (file filter in `build()`)
- Test: `tests/test_knowledge.py` (extend `setUp` fixtures + new method), `tests/test_collections.py:31,38` (loop lists)

**Interfaces:**
- Consumes: nothing (foundation task).
- Produces: `LIBRARIES` includes `'ccpp'`; `build()` admits files whose suffix is in `('.c','.config','.cfg','.cmake','.sh','.runconfig','.jl','.inc','.meta')` or whose lowercased name is `readme`. Tasks 2-5 rely on this filter.

- [ ] **Step 1: Write the failing tests**

In `tests/test_knowledge.py`, replace the `setUp` fixture block so it also creates a `protos/` subdirectory holding a bare `README`, a `.config` file and a binary `.nc` (dedicated subdirectory so the new `protos` example entry cannot re-ingest the other fixtures and break `test_kind_and_version_filters`), and append a new test method to the `Tests` class (insert after `test_unrecognized_routine_keeps_file`, before `test_new_libraries_accepted`):

```python
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
```

New test method:

```python
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
```

In `tests/test_collections.py`, extend both loops (lines ~31 and ~38) to include `ccpp`:

```python
        for library,version in [('kokkos','snapshot-test'),('kokkos-kernels','5.2.2'),('esmf','8.9.1'),('nws-hpc-standards','11.0.0'),('jedi','snapshot-test'),('ccpp','snapshot-test')]:
```

```python
        for library in ('esmf','kokkos','kokkos-kernels','nws-hpc-standards','jedi','ccpp'):
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run python -m unittest tests.test_knowledge tests.test_collections -v`
Expected: `test_extended_whitelist_admits_configs_skips_binaries` FAILs (README/config not indexed — search returns []), `test_library_isolation` FAILs with `ValueError: Unknown library` for ccpp.

- [ ] **Step 3: Implement**

In `knowledge.py` line 10:

```python
LIBRARIES = ('esmf','kokkos','kokkos-kernels','nws-hpc-standards','jedi','ccpp')
```

In `knowledge.py` line 157, replace the filter line with (single logical line, keep style):

```python
                if not file.is_file() or file.suffix.lower() not in ('.html','.htm','.f90','.f','.f95','.f03','.f08','.md','.rst','.cpp','.hpp','.h','.cc','.cxx','.txt','.yaml','.yml','.rc','.mk','.c','.config','.cfg','.cmake','.sh','.runconfig','.jl','.inc','.meta') and file.name.lower() not in ('makefile','cmakelists.txt','readme'): continue
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run python -m unittest tests.test_knowledge tests.test_collections -v`
Expected: all PASS (including the pre-existing isolation tests now covering ccpp).

- [ ] **Step 5: Verify existing index is untouched and full suite green**

Run: `uv run python -m unittest discover -s tests -t .`
Expected: `Ran 26 tests ... OK` (25 + 1 new). The real corpus has no README/.c/.config/.cfg/.inc/.meta files, so no re-ingest is needed in this task; do NOT commit `data/nuopc.sqlite3` here.

- [ ] **Step 6: Commit**

```bash
git add knowledge.py tests/test_knowledge.py tests/test_collections.py
git commit -m "Extend ingest whitelist for prototypes and CCPP; add ccpp library"
```

---

### Task 2: `get_ccpp_context` tool + server wiring

**Files:**
- Modify: `server.py` (new tool after `get_jedi_context`, `search_docs` docstring:23, FastMCP instructions:14-19)
- Test: `tests/smoke_mcp.py` (tool set + call), `tests/test_release_corpus.py` untouched here

**Interfaces:**
- Consumes: `knowledge.search(query,'documentation',limit,library='ccpp')` (works once Task 4-5 ingest ccpp data; the tool itself only needs `LIBRARIES` from Task 1 to be valid).
- Produces: MCP tool `get_ccpp_context(query:str, limit:int=4) -> dict` with keys `collections` (dict with single `'ccpp'` key), `workflow` (4-item list), `note` (str). Task 5's smoke tests call it.

- [ ] **Step 1: Add the tool and update strings in `server.py`**

Insert after `get_jedi_context` (before `list_collections`):

```python
@mcp.tool(annotations=READ_ONLY)
def get_ccpp_context(query:str,limit:int=4)->dict:
    """Retrieve CCPP (Common Community Physics Package) technical documentation matches. Rolling main snapshot of NCAR/ccpp-doc; verify against the CCPP framework actually built and fetch full sections before implementing."""
    if not 1<=limit<=8:raise ValueError('limit 1-8')
    return {'collections':{'ccpp':knowledge.search(query,'documentation',limit,library='ccpp')},
        'workflow':['Fetch complete sections with get_section, following next_offset until read.',
                    'When a section lists included_code (the scheme templates), retrieve it with get_routine.',
                    'Verify conventions against the CCPP framework and physics versions actually in your build; this snapshot tracks main.',
                    'Cite section URLs and RST line ranges from the result metadata.'],
        'note':'Rolling main snapshot, not release-certified; the upstream repository has no license file. Documentation code blocks are retained verbatim.'}
```

Update `search_docs` docstring (line 23) library list:

```python
    """Find documentation sections scoped by library: esmf, kokkos, kokkos-kernels, nws-hpc-standards, jedi, ccpp. Version defaults to the sole indexed version for that library. Fetch selected IDs using get_section before implementing."""
```

Append to the FastMCP instructions string (after the NWS/JEDI sentence):

```python
 ' For CCPP physics-framework questions call get_ccpp_context; it is a rolling main snapshot with no upstream license file, so verify against the CCPP version actually built.'
```

- [ ] **Step 2: Update `tests/smoke_mcp.py` tool set and add a call**

In the tools-list assert, add `'get_ccpp_context'` to the expected set. After the `jedi` block, add:

```python
                ccpp=await call('get_ccpp_context',{'query':'scheme template'})
                assert 'collections' in ccpp and 'ccpp' in ccpp['collections']
```

Change the final print to: `print('All eleven MCP tools passed real stdio smoke test')`.

Note: the smoke DB is the synthetic fixture (esmf-only), so `knowledge.search(...,library='ccpp')` returns `[]` — the call must still succeed with `isError` false. `search()` raises `ValueError('Unknown library')` only for labels outside `LIBRARIES`; `ccpp` is inside since Task 1, and an empty result set is returned when the library has no indexed versions (`if not versions:return []`). Verify this behavior when you run Step 3.

- [ ] **Step 3: Run the smoke test to verify it passes**

Run: `uv run python tests/smoke_mcp.py`
Expected: `All eleven MCP tools passed real stdio smoke test`.

Run: `uv run python -m unittest discover -s tests -t .`
Expected: `Ran 26 tests ... OK`.

- [ ] **Step 4: Commit**

```bash
git add server.py tests/smoke_mcp.py
git commit -m "Add get_ccpp_context tool and eleven-tool smoke coverage"
```

---

### Task 3: `fetch_corpus.py` prototypes support

**Files:**
- Modify: `fetch_corpus.py` (constants after:17, `main()` argparse + clone/copy/swap/manifest)
- Test: manual dry-run in Step 4 (the fetcher needs network; unit tests for its helpers live in Task 4's file)

**Interfaces:**
- Consumes: Task 1's whitelist (so prototype README/.config files index later).
- Produces: `corpus/nuopc-app-prototypes/` tree and a 4th esmf manifest entry `{"name":"nuopc-app-prototypes", ...}` (exact JSON in Step 3). Task 5 ingests it.

- [ ] **Step 1: Add constants**

After `MANUALS=(...)` in `fetch_corpus.py`:

```python
PROTOS_REPO='https://github.com/esmf-org/nuopc-app-prototypes.git'
PROTOS_REF='patch/8.9.1'
PROTOS_COMMIT='1645f4471da271e518213ceb574b0ada0ff3a169'
```

- [ ] **Step 2: Add the CLI flag**

Inside `main()`, after the `--skip-manuals` argument:

```python
    parser.add_argument('--protos-repo',type=Path,help='Existing clean checkout at the pinned prototypes patch/8.9.1 commit')
```

- [ ] **Step 3: Clone, verify, stage, swap, and manifest the prototypes**

After the existing ESMF license-copy block (`for path in license_files:shutil.copy2(...)`) and BEFORE `target=ROOT/'corpus'`, insert:

```python
        protos=args.protos_repo.resolve() if args.protos_repo else staging/'protos-repo'
        if not args.protos_repo:
            subprocess.run(['git','clone','--depth','1','--branch',PROTOS_REF,PROTOS_REPO,str(protos)],check=True)
        if run(['git','-C',str(protos),'rev-parse','HEAD'])!=PROTOS_COMMIT:raise ValueError('Prototypes checkout does not match pinned patch/8.9.1 commit')
        if run(['git','-C',str(protos),'status','--porcelain']):raise ValueError('Prototypes checkout has modifications; refusing to snapshot it')
        shutil.copytree(protos,staging/'nuopc-app-prototypes',ignore=shutil.ignore_patterns('.git'))
        if not any((staging/'nuopc-app-prototypes').rglob('*.F90')):raise ValueError('Prototypes tree contains no Fortran sources')
```

(The clone lands in a distinct `protos-repo` directory so the `.git`-free copy never collides with its own source.)

Then in the swap loop, extend the directory tuple. Replace:

```python
        for name in ('manuals','examples','src'):
```

with:

```python
        for name in ('manuals','examples','src','nuopc-app-prototypes'):
```

In the manifest-building section, after the `for name,kind in [('examples','example'),('src','implementation')]:` loop appends the two esmf/NUOPC entries, append:

```python
        sources.append({'name':'nuopc-app-prototypes','path':'corpus/nuopc-app-prototypes','version':'8.9.1',
            'kind':'example','url':f'https://github.com/esmf-org/nuopc-app-prototypes/blob/{PROTOS_COMMIT}',
            'revision':PROTOS_COMMIT,'managed':True,
            'version_basis':'patch/8.9.1 branch tip verified by commit; no 8.9.1 tag exists upstream; repository has no license file (sources carry the Illinois-NCSA header)'})
```

- [ ] **Step 4: Dry-run the fetcher against the pinned ref**

Run (network required):

```bash
cd /Users/barry/Documents/docs-mcp && uv run fetch_corpus.py --skip-manuals
```

Expected: prints `Pinned corpus ready. Run uv run ingest.py`; `corpus/nuopc-app-prototypes/` exists; `corpus.json` now has 11 sources — `fetch_corpus.py` rewrites only the esmf group and preserves the four kokkos/nws/jedi entries, so the file keeps all 10 prior entries plus the new prototypes entry. Verify:

```bash
python3 -c "
import json,pathlib
s=json.load(open('corpus.json'))['sources']
print(len(s),[e['name'] for e in s])
assert any(e['name']=='nuopc-app-prototypes' for e in s)
assert not (pathlib.Path('corpus/nuopc-app-prototypes/.git').exists())
dirs=[p for p in pathlib.Path('corpus/nuopc-app-prototypes').iterdir() if p.is_dir()]
print('protos dirs:',len(dirs))
assert len(dirs)>=51
"
```

Expected: `11 [...]` including `nuopc-app-prototypes`; `protos dirs: 52` (51 prototype directories plus the repo's `.github`).

- [ ] **Step 5: Confirm no ingest yet, commit corpus + fetcher + manifest**

```bash
git add fetch_corpus.py corpus.json corpus/nuopc-app-prototypes
git commit -m "Fetch NUOPC application prototypes pinned to patch/8.9.1"
```

Do NOT run `ingest.py` in this task; Task 5 reindexes once with both new sources.

---

### Task 4: `fetch_standards.py` CCPP support (config generalisation)

**Files:**
- Modify: `fetch_standards.py` (docstring, DEFAULT, `copy_markdown`, `read_doc_release`, `main()`)
- Test: `tests/test_fetch_standards.py` (new/updated helper tests)

**Interfaces:**
- Consumes: Task 1 (`ccpp` in `LIBRARIES`, `.inc`/`.meta` whitelisted).
- Produces: `corpus/ccpp/source/` + `corpus/ccpp/included-code/` trees; two manifest entries `ccpp-docs` (documentation, `target_release`) and `ccpp-included-code` (example); `standards-lock.json` gains a `ccpp` key. Task 5 ingests.

- [ ] **Step 1: Write the failing helper tests**

In `tests/test_fetch_standards.py`, update the existing `copy_markdown` call to the new signature and add two tests. Replace the whole `FetchStandardsHelpers` class body's first test method and append:

```python
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
    def test_read_doc_release_uses_conf_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=Path(tmp)
            conf=repo/'CCPPtechnical'/'source'/'conf.py';conf.parent.mkdir(parents=True)
            conf.write_text("version = '6.0'\nrelease = '6.0.0'\n")
            self.assertEqual(fetch_standards.read_doc_release(repo,'fallback',conf_path='CCPPtechnical/source/conf.py'),'6.0.0')
            self.assertEqual(fetch_standards.read_doc_release(repo,'fallback',conf_path='nope/conf.py'),'fallback')
```

- [ ] **Step 2: Run to verify failures**

Run: `uv run python -m unittest tests.test_fetch_standards -v`
Expected: new tests FAIL (`copy_markdown() got an unexpected keyword argument 'exts'`, `read_doc_release() got an unexpected keyword argument 'conf_path'`).

- [ ] **Step 3: Generalise `fetch_standards.py`**

Docstring line 1:

```python
"""Import NWS-HPC standards, JEDI and CCPP documentation, preserving other corpus collections."""
```

Replace the `DEFAULT` table with:

```python
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
}
```

Replace `copy_markdown`:

```python
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
```

Replace `read_doc_release`:

```python
def read_doc_release(repo,fallback,conf_path='docs/conf.py'):
    """Read the Sphinx release from the checked-out conf.py at conf_path; fall back if absent."""
    conf=repo/conf_path
    if conf.is_file():
        match=re.search(r"^release\s*=\s*['\"]([^'\"]+)['\"]",conf.read_text(encoding='utf-8',errors='replace'),re.M)
        if match:return match.group(1)
    return fallback
```

In `main()`:

- argparse: add `parser.add_argument('--ccpp-repo',type=Path,help='Use a local CCPP docs checkout')` and update `--latest` help to `'Refresh to the newest NWS release tag, current JEDI develop, and current CCPP main; record new commits'`.
- The `supplied=` line becomes:

```python
            supplied={'nws-hpc-standards':args.nws_repo,'jedi':args.jedi_repo,'ccpp':args.ccpp_repo}[library]
```

- `--latest` ref selection: `ref=latest_release(config['repo']) if library=='nws-hpc-standards' else config['branch']` already yields `'main'` for ccpp — unchanged.
- doc_release read line: `if 'conf_path' in config:config['doc_release']=read_doc_release(repo,config.get('doc_release',''),config['conf_path'])`.
- Copy call: replace `count=copy_markdown(source,target/'source')` with:

```python
            source=repo/config['doc_dir']
            if not source.is_dir():raise ValueError(f'{library}: docs directory {config["doc_dir"]} missing')
            count=copy_markdown(source,target/'source',exts=tuple(config['exts']),skip_dirs=tuple(config.get('skip_dirs',('_build','venv','.git','__pycache__'))))
            if count==0:raise ValueError(f'{library}: no documentation files found')
```

(delete the old `source=repo/'docs'` two-line block above it).

- License branch: replace the `if library=='jedi': ... else: ...` block with:

```python
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
                destination=target/'included-code'/Path(reference).name
                destination.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(file,destination);included_files.append(destination)
```

- Basis + entry building: replace the single `basis=...` ternary and `entry={...}` append with:

```python
            if library=='nws-hpc-standards':
                basis='Official release tag '+ref+'; matches RTD /en/stable/'
            elif library=='jedi':
                basis='Rolling develop snapshot matching RTD /en/latest/; docs/conf.py declares release '+config.get('doc_release','')+'; not release-certified'
            else:
                basis=('Rolling main snapshot matching RTD /en/latest/; conf.py declares release '
                       +config.get('doc_release','')+'; not release-certified; repository has no license file')
            entry={'name':library+'-docs','path':f'corpus/{library}/source','library':library,
                'version':config['version'],'kind':'documentation','managed':True,'revision':commit,
                'url':f'https://github.com/{config["repo"]}/blob/{commit}/{config["doc_dir"]}','version_basis':basis}
            if 'doc_release' in config:entry['target_release']=config.get('doc_release')
            sources.append(entry)
            if included_files:
                sources.append({'name':library+'-included-code','path':f'corpus/{library}/included-code','library':library,
                    'version':config['version'],'kind':'example','managed':True,'revision':commit,
                    'url':f'https://github.com/{config["repo"]}/blob/{commit}/{config["doc_dir"]}','version_basis':'Files referenced by documentation literalinclude directives'})
```

- Final print: `print('NWS-HPC standards, JEDI and CCPP documentation imported. Run uv run ingest.py')`.

- [ ] **Step 4: Run helper tests**

Run: `uv run python -m unittest tests.test_fetch_standards -v`
Expected: all PASS (5 tests).

- [ ] **Step 5: Dry-run the fetcher against pinned commits (network)**

Run: `cd /Users/barry/Documents/docs-mcp && uv run fetch_standards.py`

Expected: prints the import success line. Verify:

```bash
python3 -c "
import json,pathlib
s=json.load(open('corpus.json'))['sources']
names=[e['name'] for e in s];print(len(s),names)
assert 'ccpp-docs' in names and 'ccpp-included-code' in names
lock=json.load(open('standards-lock.json'));assert lock['ccpp']['commit']=='a2f65334fda991fb7aa6a37716c003533529370e'
docs=list(pathlib.Path('corpus/ccpp/source').rglob('*'));print('ccpp docs files:',len([d for d in docs if d.is_file()]))
inc=list(pathlib.Path('corpus/ccpp/included-code').iterdir());print('included:',sorted(p.name for p in inc))
assert len([d for d in docs if d.is_file()])==19 and len(inc)==2
# nws/jedi unchanged
assert list(pathlib.Path('corpus/nws-hpc-standards/source').rglob('*.rst'))
assert (pathlib.Path('corpus/jedi/COPYING')).is_file()
"
```

Expected: `13 [...]` (11 + 2 new); `ccpp docs files: 19`; `included: ['scheme_template.F90','scheme_template.meta']`.

- [ ] **Step 6: Commit**

```bash
git add fetch_standards.py tests/test_fetch_standards.py corpus.json standards-lock.json corpus/ccpp
git commit -m "Generalise standards fetcher config and import CCPP docs snapshot"
```

---

### Task 5: Reindex, regression tests, docs, image, push

**Files:**
- Modify: `data/nuopc.sqlite3` (rebuilt), `tests/test_release_corpus.py`, `tests/test_collections.py` (StandardsReleaseTests + ccpp), `tests/smoke_docker.py`, `README.md`, `.github/copilot-instructions.md`

**Interfaces:**
- Consumes: Tasks 1-4 (whitelist, tool, both corpus trees).
- Produces: final index with counts `esmf 3159` (doc 1764 / example 1039 / impl 356), `ccpp 140` (doc 137 / example 3), others unchanged.

- [ ] **Step 1: Reindex**

Run: `cd /Users/barry/Documents/docs-mcp && uv run ingest.py`
Expected: JSON with six collections; `units` counts include `example: 1088` (18+1021+46+3 → note kokkos-kernels examples are also `example` kind, so total example = 18+1021+46+3 = 1088) and `documentation: 6028` (1764+1610+595+22+1900+137). If counts differ, STOP and reconcile before proceeding.

- [ ] **Step 2: Write the real-corpus regression tests**

In `tests/test_release_corpus.py`, append to `ReleaseTests`:

```python
    def test_prototypes_are_discoverable_examples(self):
        hits=self.store.search('SetServices','example',8)
        protos=[hit for hit in hits if 'nuopc-app-prototypes' in hit['source']]
        self.assertTrue(protos)
        result=self.store.get(protos[0]['id'])
        self.assertEqual(result['provenance']['revision'],'1645f4471da271e518213ceb574b0ada0ff3a169')
        self.assertIn('1645f4471da2',result['url'])
        readme=[hit for hit in self.store.search('connector options','example',8) if hit['source'].endswith('AtmOcnConOptsProto/README')]
        self.assertTrue(readme)
        config=[hit for hit in self.store.search('ATM_petlist','example',8) if hit['source'].endswith('AtmOcnPetListProto/nuopcRun.config')]
        self.assertTrue(config)
```

In `tests/test_collections.py`, in `StandardsReleaseTests` append (guarded by the existing class-level skipUnless on standards-lock.json):

```python
    def test_ccpp_scheme_templates_resolve_as_included_code(self):
        lock=json.loads((ROOT/'standards-lock.json').read_text())
        revision=lock['ccpp']['commit'];version=lock['ccpp']['version']
        hits=self.store.search('Compliant Physics Parameters','documentation',6,library='ccpp',version=version)
        self.assertTrue(hits)
        page=[h for h in hits if h['source'].endswith('CompliantPhysicsParams.rst')][0]
        names=set();offset=0
        while True:
            result=self.store.get(page['id'],offset,include_subsections=True,max_characters=32000)
            names.update(i['source'].split('/')[-1] for i in result['included_code'])
            self.assertEqual([m for m in result['missing_included_code'] if m.split('/')[-1] in ('scheme_template.F90','scheme_template.meta')],[])
            if result['next_offset'] is None:break
            offset=result['next_offset']
        self.assertEqual(names,{"scheme_template.F90","scheme_template.meta"})
        self.assertIn(revision,self.store.get(page['id'])['provenance']['url'])
    def test_ccpp_auxiliary_files_are_whole_file_units(self):
        for query,suffix in (('prolog','.inc'),('ccpp_physics','.txt')):
            hits=self.store.search(query,'documentation',8,library='ccpp')
            self.assertTrue([h for h in hits if h['source'].endswith(suffix)],f'no {suffix} unit for {query}')
```

Add a per-collection count isolation test to `tests/test_collections.py` as a new class (skipUnless corpus.json + both locks exist):

```python
@unittest.skipUnless((ROOT/'corpus.json').exists() and (ROOT/'standards-lock.json').exists() and (ROOT/'kokkos-lock.json').exists(),'Full corpus not imported')
class PrototypeAndCcppCountTests(unittest.TestCase):
    def test_counts_isolated_to_new_sources(self):
        import sqlite3
        db=ROOT/'data'/'nuopc.sqlite3'
        con=sqlite3.connect(f'file:{db}?mode=ro',uri=True)
        counts={(r[0],r[1],r[2]):r[3] for r in con.execute('SELECT library,version,kind,count(*) FROM units GROUP BY 1,2,3')}
        con.close()
        self.assertEqual(counts[('esmf','8.9.1','documentation')],1764)
        self.assertEqual(counts[('esmf','8.9.1','implementation')],356)
        self.assertEqual(counts[('esmf','8.9.1','example')],1039)
        self.assertEqual(counts[('kokkos','snapshot-3cf2e0638b24','documentation')],1610)
        self.assertEqual(counts[('kokkos-kernels','5.2.2','documentation')],595)
        self.assertEqual(counts[('kokkos-kernels','5.2.2','example')],46)
        self.assertEqual(counts[('nws-hpc-standards','11.0.0','documentation')],22)
        self.assertEqual(counts[('jedi','snapshot-7cd222915252','documentation')],1900)
        self.assertEqual(counts[('ccpp','snapshot-a2f65334fda9','documentation')],137)
        self.assertEqual(counts[('ccpp','snapshot-a2f65334fda9','example')],3)
```

- [ ] **Step 3: Run the suite and smoke test**

Run: `uv run python -m unittest discover -s tests -t .`
Expected: `Ran 32 tests ... OK` (26 after Task 1 + 2 after Task 4 + 1 prototypes + 2 ccpp + 1 counts in this task). If any count assertion fails, the index is stale — rerun ingest.

Run: `uv run python tests/smoke_mcp.py`
Expected: `All eleven MCP tools passed real stdio smoke test`.

- [ ] **Step 4: Update `tests/smoke_docker.py`**

In `REQUESTS`, append after the jedi call (id 9):

```python
    call(9, "get_ccpp_context", {"query": "scheme template", "limit": 4}),
```

`EXPECTED_IDS = {1, 2, 3, 4, 5, 6, 7, 8, 9}`. In `test_tools_list`, add `"get_ccpp_context"` to the expected set. In `test_list_collections`, change the esmf assertion to `3159` and add:

```python
        self.assertEqual(units.get(("ccpp", "snapshot-a2f65334fda9")), 140)
```

In `test_search_and_context`, optionally assert the ccpp payload has the collections key (add a resp[9] check mirroring the nws/jedi pattern in the smoke_mcp style — keep minimal):

```python
        ccpp = _payload(resp[9]["result"])
        self.assertIn("collections", ccpp)
        self.assertIn("ccpp", ccpp["collections"])
```

- [ ] **Step 5: Update `README.md`**

- Intro: "five curated collections — ESMF/NUOPC, Kokkos, Kokkos Kernels, NWS-HPC production standards and JEDI" → "six curated collections — ESMF/NUOPC, Kokkos, Kokkos Kernels, NWS-HPC production standards, JEDI and CCPP".
- Collections table: `esmf` row Content gains ", and the 51 NUOPC application prototypes (`nuopc-app-prototypes`, patch/8.9.1 commit `1645f4471da2...`)"; esmf Units `2138` → `3159`. Add a `ccpp` row: `| \`ccpp\` | CCPP technical documentation (\`NCAR/ccpp-doc\` main commit \`a2f65334fda991fb7aa6a37716c003533529370e\`), matching RTD \`/en/latest/\` | \`snapshot-a2f65334fda9\` | 140 |`.
- The "All five collections" sentence → "All six collections"; "Unit counts ... five" phrasing updated; add prototypes pin to the lock sentence (`fetch_corpus.py` pins them in `corpus.json`).
- Provenance paragraph: note the prototypes repo has no license file (sources carry the Illinois-NCSA header) and CCPP likewise has none.
- New `### CCPP` subsection after `### NWS-HPC standards and JEDI`: rolling main snapshot, `target_release` 6.0.0 informational, `get_ccpp_context`, an "Ask Copilot" example prompt, and the two `literalinclude` scheme templates resolve via `included_code`.
- Refreshing section: ESMF block notes the prototypes clone (`--protos-repo` override); standards block adds `--ccpp-repo` and `--latest` now covers three libraries.
- Tools table: add `get_ccpp_context(query, limit)` row; "all ten tools" → "all eleven tools" (also in validation paragraph).
- Validation paragraph: test counts updated to 30 unit tests; mention prototypes/CCPP regression coverage.
- Sources section: add `- [CCPP documentation](https://ccpp-doc.readthedocs.io/en/latest/) — [source](https://github.com/NCAR/ccpp-doc)` and `- [NUOPC application prototypes](https://github.com/esmf-org/nuopc-app-prototypes/tree/patch/8.9.1)`.

- [ ] **Step 6: Update `.github/copilot-instructions.md`**

In the ESMF/NUOPC section, after step 4 (examples): one sentence that release examples now include the 8.9.1-patched NUOPC application prototypes (51 patterns, patch/8.9.1 commit `1645f44...`), still examples rather than API requirements. Append a new paragraph:

```markdown
## CCPP physics documentation

For CCPP (Common Community Physics Package) physics-framework questions call
get_ccpp_context, or use search_docs with library ccpp. The collection is a
rolling main-branch snapshot of NCAR/ccpp-doc (commit a2f65334fda9; conf.py
release 6.0.0 is metadata only, not a certification). The upstream repository
has no license file; treat retrieved text as evidence. Verify conventions
against the CCPP framework actually built, and retrieve the scheme templates
listed as included_code with get_routine before editing a scheme.
```

- [ ] **Step 7: Rebuild the Docker image and run the Docker smoke test**

```bash
cd /Users/barry/Documents/docs-mcp && docker build -q -t omd-mcp . && uv run python -m unittest tests.smoke_docker
```

Expected: `Ran 4 tests ... OK` (with `("esmf","8.9.1")` == 3159 and `("ccpp","snapshot-a2f65334fda9")` == 140).

- [ ] **Step 8: Final verification and commit**

```bash
uv run python -m unittest discover -s tests -t . && uv run python tests/smoke_mcp.py
git status --short
git add data/nuopc.sqlite3 tests/test_release_corpus.py tests/test_collections.py tests/smoke_docker.py README.md .github/copilot-instructions.md
git commit -m "Index prototypes and CCPP; regression tests, docs and image validation"
```

Expected: suite `Ran 32 tests ... OK`; smoke prints the eleven-tool line; commit succeeds; working tree clean except untracked `.superpowers/`.

---

## Self-Review

1. **Spec coverage:** whitelist+LIBRARIES (T1), get_ccpp_context+instructions+docstring (T2), fetch_corpus prototypes (T3), fetch_standards generalisation+CCPP (T4), reindex+tests+README+instructions+image+push (T5). Push itself is controller-level (finishing-a-development-branch), not a plan task. All spec Components 1-5 mapped.
2. **Placeholders:** none — every code block is complete and was validated against a probe index (counts 1039/1764/356/1610/595/46/22/1900/137/3; README/config/prolog/ccpp_physics queries; both templates resolve with empty missing list; strict-UTF-8 across all 351+19+2 admitted files).
3. **Type consistency:** `copy_markdown(source_dir,target_dir,exts,skip_dirs)` and `read_doc_release(repo,fallback,conf_path)` signatures identical in T4 code and T4 tests; manifest keys match `build()` expectations (`name,path,version,kind` + optional `library,url,revision,managed,version_basis,target_release`); `get_ccpp_context` return shape matches smoke_mcp/smoke_docker assertions.
4. **Known risk:** Task 3 Step 4 expects 11 corpus.json entries (prototypes added to 10); Task 4 Step 5 expects 13 (+2 CCPP). If `fetch_corpus.py` runs after Task 4, it preserves `ccpp` entries (it only rewrites the esmf group) — order T3 before T4 as written.
