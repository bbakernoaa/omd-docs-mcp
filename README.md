# OMD Library Docs MCP Server

A local, read-only documentation retrieval server for GitHub Copilot Agent
mode. **omd** indexes seven curated collections — ESMF/NUOPC, Kokkos, Kokkos
Kernels, NWS-HPC production standards, JEDI, CCPP and CCPP-SCM — and retrieves complete
manual sections, Fortran routines and C++ examples with release provenance
and citations. It separates API requirements, examples, framework
implementation, and your application code.

There is no generated briefing or local LLM in the retrieval path: the coding
agent gets original evidence and is instructed to read it before making
changes. This replaces the earlier general PDF/Ollama server.

## Collections

All seven collections are bundled in the committed index and pinned in the
lock files; nothing refreshes automatically.

| Collection | Content | Version label | Units |
| --- | --- | --- | --- |
| `esmf` | NUOPC Layer Reference Manual (9 pages), Building a NUOPC Model guide (6 files), Fortran Reference Manual (10 files), NUOPC model/cap **and driver** examples, and the NUOPC framework implementation — official ESMF **8.9.1** release sources — plus the 51 NUOPC application prototypes from the separate `nuopc-app-prototypes` repository (patch/8.9.1 branch commit `1645f4471da271e518213ceb574b0ada0ff3a169`) | `8.9.1` | 3159 |
| `kokkos` | Kokkos core wiki/docs repository at commit `3cf2e0638b2419f4631fa85ea2b9aca47004dc18` | `snapshot-3cf2e0638b24` | 1610 |
| `kokkos-kernels` | Kokkos Kernels release documentation at commit `30ad8eddc07f98f73ad22d5ed59cbea78277b03e`, plus referenced C++ examples | `5.2.2` | 641 |
| `nws-hpc-standards` | NWS/WCOSS NCEP implementation standards, tag `v11.0.0` (commit `d0e8f079b66891d39fe7494a1c68bd7c77639425`), matching RTD `/en/stable/` | `11.0.0` | 22 |
| `jedi` | JEDI data assimilation documentation, develop commit `7cd222915252711893bf341bc1b67ffef3b2824a`, matching RTD `/en/latest/` | `snapshot-7cd222915252` | 1900 |
| `ccpp` | CCPP technical documentation (`NCAR/ccpp-doc` main commit `a2f65334fda991fb7aa6a37716c003533529370e`), matching RTD `/en/latest/` | `snapshot-a2f65334fda9` | 140 |
| `ccpp-scm` | CCPP Single Column Model (SCM) technical guide (`NCAR/ccpp-scm` main commit `a52680b013066e0f3135d63ae587ced18a434e86`), matching RTD `/en/latest/` | `snapshot-a52680b01306` | 95 |

Unit counts come from the committed index; `list_collections` reports them
live. Kokkos pins are recorded in `kokkos-lock.json` (stable releases checked
2026-10-05), NWS/JEDI/CCPP pins in `standards-lock.json` (checked 2026-10-06),
and `fetch_corpus.py` pins the NUOPC application prototypes in `corpus.json`.

The importer verified each clean checkout and the official release labels.
The ESMF examples are release examples, not examples compiled/tested by this
project. HTML is preferred over PDF because API boundaries and section anchors
are explicit, keeping original signatures, argument descriptions and examples
together. The ESMF source license is in `corpus/LICENSE`; the JEDI license is
`corpus/jedi/COPYING` and the NWS disclaimer is
`corpus/nws-hpc-standards/DISCLAIMER.md`. The prototypes repository and
`NCAR/ccpp-doc` do not ship a top-level license file in the fetched trees;
prototype source files carry the Illinois-NCSA header.

### Kokkos

Core documentation is maintained separately from the library release. Its
snapshot is **not certified as a 5.2.2-only manual** and may describe newer or
experimental APIs. Always check version-added notes and your installed version.
No compatibility claim between ESMF and Kokkos is inferred by this server.

ReStructuredText and Markdown documentation are indexed as original sections,
including signatures, parameters and code blocks. Source citations point to
commit-specific GitHub files and line ranges. Formatting directives, substitutions
and cross-references remain in their original form; no Sphinx build is executed.
Kernels `literalinclude` examples are copied from the same release and exposed as
`included_code` IDs in `get_section`; read those using `get_routine`.
Two upstream example references (`apply_householder.cpp`, `householder.cpp`) could
not be resolved in the release checkout. They are recorded in manifest provenance
and returned as `missing_included_code` on affected sections.

Ask Copilot:

> Use get_kokkos_context to find the documentation for KokkosBlas::gemm. Read the
> full section and examples, verify execution space and layout requirements,
> then apply it to my code and run the relevant backend tests.

Or select the collection explicitly:

```text
search_docs(query="Kokkos::parallel_for", library="kokkos")
search_docs(query="KokkosSparse::spmv", library="kokkos-kernels", version="5.2.2")
```

`get_nuopc_context` still searches only ESMF 8.9.1. Library isolation prevents
unrelated documentation from filling its results. `get_kokkos_context` returns
separate core and Kernels result lists. `list_collections` shows available version
labels. If multiple versions of one library are indexed, searches require an
explicit version instead of silently mixing them.

### NWS-HPC standards and JEDI

The NWS collection is a pinned release-tag snapshot of an operational policy
document that NCO updates over time. The JEDI collection is a **rolling develop
snapshot**, not certified against any single JEDI software release; its
`docs/conf.py` declares release `8.0.0` (recorded as `target_release`). Verify
against the version you actually build. Neither repo uses `literalinclude`, so no
included-code retrieval applies to these collections.

Ask Copilot:

> Use get_nws_context to find the standard environment variables and the
> compath.py utility. Read the full section and cite the RST line range before
> I adjust my J-job.

> Use get_jedi_context to look up ObsGroup and ObsSpace conventions. Read the
> full conventions section, then check it against the JEDI version in my build.

### CCPP

The CCPP collection is a rolling snapshot of the `NCAR/ccpp-doc` main branch.
Its `conf.py` declares release `6.0.0`, but that `target_release` value is
informational metadata rather than certification of a frozen CCPP framework
release. Verify conventions against the CCPP framework actually built in your
environment. Two `literalinclude` scheme templates are indexed as
`included_code` and can be retrieved with `get_routine`.

Ask Copilot:

> Use get_ccpp_context to find the scheme template guidance for adding a new
> CCPP physics scheme. Read the full section, retrieve the included templates,
> and compare the conventions to the framework version in my checkout.

### CCPP-SCM

The CCPP-SCM collection is a rolling snapshot of the `NCAR/ccpp-scm` main branch.
Its `conf.py` declares release `7.0.1`, but that `target_release` value is
informational metadata rather than certification of a frozen release. Verify
conventions against the SCM framework actually built in your environment. Three
`literalinclude` case header/namelist targets are indexed as `included_code` and
can be retrieved with `get_routine`.

Ask Copilot:

> Use get_ccpp_scm_context to find the case setup guidance for SCM runs. Read
> the full section, retrieve the included case headers/namelists, and compare
> the conventions to the SCM version in my checkout.

## Quick start

With Docker only (no local Python or uv), build the image once from this
repository and Copilot runs the server in a read-only container:

```sh
docker build -t omd-mcp .
```

`.vscode/mcp.json` launches `docker run -i --rm --read-only --pull=never
--memory=512m omd-mcp`. Enable it from `MCP: List Servers`. The image bundles the
committed `data/nuopc.sqlite3`, so a fresh clone plus Docker is enough.

**Refreshing the index.** The container serves the index baked at build time.
After any `fetch_corpus.py` / `fetch_kokkos.py` / `fetch_standards.py` +
`ingest.py` refresh, commit `data/nuopc.sqlite3` and rebuild the image:

```sh
uv run ingest.py
git add data/nuopc.sqlite3 && git commit -m "Reindex"
docker build -t omd-mcp .
```

Skipping the rebuild leaves the running container on a stale index; the
container cannot detect this. The steps below use uv directly and remain the
developer path.

Install Python 3.11+ and [uv](https://docs.astral.sh/uv/getting-started/installation/).
Clone this repository, open it in VS Code, and run in its terminal:

```sh
uv sync
uv run ingest.py
```

The bundled sources let you index without downloading manuals again. Python
package installation requires internet access. No ESMF build is needed for indexing.

Start **omd** from `.vscode/mcp.json` or `MCP: List Servers`. Enable its tools
in Copilot Agent mode. To select a specific tool, type `#` and select it from
Copilot autocomplete. Try:

> Use get_nuopc_context with focus driver to inspect how NUOPC_DriverAddComp is
> used in ESMF 8.9.1. Read all applicable API overloads and the complete example
> routines before suggesting changes to my driver. Cite the sections and lines.

For a cap:

> Use get_nuopc_context with focus cap to check my initialization and field
> advertisement/realization. Read the API and lifecycle sections plus release
> examples. Inspect my existing cap before editing; compile and run its tests.

Copilot still uses its selected model. Retrieved excerpts can be transmitted
as part of Copilot's context; this is not an offline coding-agent workflow.

## Use in your actual model repository

The included `${workspaceFolder}` configuration assumes this MCP project itself
is open. When working on your model, merge the following into **your model's**
`.vscode/mcp.json`, preserving its existing servers:

```json
{
  "servers": {
    "omd": {
      "type": "stdio",
      "command": "docker",
      "args": ["run", "-i", "--rm", "--read-only", "--pull=never", "--memory=512m", "omd-mcp"]
    }
  }
}
```

The image must be built from this repository first (tag it on the target
machine with `docker build -t omd-mcp /absolute/path/to/docs-mcp`), then
any workspace can point `mcp.json` at the tag. `docker` must be on VS Code's
PATH; restart VS Code after installation. VS Code launches the stdio container;
there is no browser endpoint or separate manual server startup step. The uv
`command`/`args` form still works for developers who prefer a local Python env.

Merge `.github/copilot-instructions.md` into the corresponding file in your model
repository. This is important: instructions inside this MCP project alone do
not become repository instructions for another workspace. They direct the agent
to retrieve authoritative evidence, compare overloads, check lifecycle assumptions,
and run your project's build/tests. Instructions steer behavior; they cannot
force the agent to comply or guarantee correct code.

## Add your cap and driver code

Append an entry to `corpus.json`'s `sources` array:

```json
{
  "name": "my-model",
  "path": "/absolute/path/to/my-model/caps-and-driver",
  "version": "8.9.1",
  "kind": "application",
  "version_basis": "Application targets ESMF 8.9.1; validate with project builds and tests"
}
```

Use a narrow directory containing the cap, driver and relevant configurations;
add additional entries for separate directories/files. Then rerun:

```sh
uv run ingest.py
```

Files are snapshotted into the index, not read live during tool calls. Re-ingest
after edits. The agent should inspect current workspace files directly as well.
The application version label is your declaration, not proof of compatibility.
No application files are included in the supplied corpus.

Supported inputs: HTML/RST/Markdown manuals, free-form Fortran source, whole-file C++
examples, text and YAML,
`.rc`/`.mk`, Makefiles and CMakeLists.txt, C sources, shell scripts, CMake files,
`.config`/`.cfg`/`.runconfig` run configurations, Julia, and CCPP `.inc`/`.meta`
fragments; bare `README` files are indexed by name. Configurations and unrecognized source
syntax retain a full-file record. A separate `corpus.example.json` shows custom
manifest entries. Paths are relative to the manifest location or absolute.

## Tools

| Tool | Purpose |
| --- | --- |
| `get_nuopc_context(query, focus, limit)` | Separate results for manuals, lifecycle references, release examples and application code; focus `cap`, `driver` or `both` |
| `search_docs(query, limit, version, library)` | Discover official/manual sections; exact API names receive heading priority |
| `search_code(query, kind, limit, version, library)` | Find routines/files; kind `example`, `application` or `implementation` |
| `get_section(section_id, offset, max_characters, include_subsections)` | Read a complete section and its nested subsections, with explicit pagination |
| `get_routine(routine_id, offset, max_characters)` | Read original routine/file text, source lines, module context and provenance |
| `get_kokkos_context(query, library, limit)` | Separate core and Kernels documentation results; library `kokkos`, `kokkos-kernels` or `both` |
| `get_nws_context(query, limit)` | NWS/WCOSS production-standards sections (env vars, file naming, delivery utilities); pinned 11.0.0 snapshot |
| `get_jedi_context(query, limit)` | JEDI data assimilation documentation; rolling develop snapshot |
| `get_ccpp_context(query, limit)` | CCPP physics-framework documentation and included scheme-template guidance; rolling main snapshot |
| `get_ccpp_scm_context(query, limit)` | CCPP Single Column Model (SCM) technical guide documentation; rolling main snapshot |
| `list_collections()` | List available library/version collections and counts |
| `list_sources()` | Inspect indexed sources, versions and evidence categories |

Search returns discovery excerpts capped at 1,800 characters. The agent must
fetch the selected sections/routines to implement from them. Parent documentation
sections include their children when `include_subsections=true`. Source routine
records identify their containing file with `parent`; retrieve that ID to inspect
imports, declarations, registration, other routines and calling context.

Fortran routine titles include the module name, for example `DRIVER::SetServices`,
to distinguish identically named model/driver routines. Module preambles are
returned as `provenance.module_context`; the complete file is always available.

Long results use `next_offset`; follow it until null. This is explicit pagination,
not silent truncation. `complete=true` means the entire unit fit in that response;
if multiple responses are needed, concatenate them in offset order. The full text
is indexed even when an excerpt/paginated result contains only part of it.
Documentation citations use release URLs and section anchors, not PDF pages.
Code citations use file paths and line ranges, plus commit-specific source URLs.

ESMF remains restricted to **8.9.1**. Every collection uses its explicit
release or documentation snapshot label; every result identifies its library
and version. Searches default to library `esmf`. For any library, an omitted
version selects its sole indexed version or requires a choice if there are
several. The default
index is `data/nuopc.sqlite3`; override it via `ingest.py --db PATH` and the server's
`DOCS_MCP_DB` environment variable. Re-ingest when upgrading this version because the index schema now includes
library scope. There is no embedding dependency. SQLite FTS5
provides keyword retrieval with title weighting and exact API-heading priority.
Natural-language queries work best when they include concrete APIs/lifecycle terms.

## Refreshing a collection

Each fetcher performs network access only when explicitly run, verifies the
pinned checkout, and rewrites `corpus.json` in place; rerun `ingest.py`
afterwards. Refreshing one collection preserves the others' entries, and a
fetcher refuses to silently overwrite custom entries — save those separately
and merge them back.

ESMF **8.9.1** manuals, examples and source:

```sh
uv run fetch_corpus.py
uv run ingest.py
```

It downloads only the three pinned 8.9.1 manual trees, clones ESMF tag v8.9.1,
checks the exact commit/clean state, and copies NUOPC examples and source. It never
fetches development HEAD or silently substitutes another release. Git is needed
for this operation. Downloads are staged; download failures leave the prior
corpus and index intact. Refresh performs file replacement once staging succeeds;
a disk failure during replacement may require rerunning the fetcher.

If you already have a clean release checkout:

```sh
uv run fetch_corpus.py --esmf-repo /path/to/esmf-v8.9.1
```

To override the pinned prototypes checkout as well:

```sh
uv run fetch_corpus.py --esmf-repo /path/to/esmf-v8.9.1 --protos-repo /path/to/nuopc-app-prototypes
```

Use `--skip-manuals` to reuse the cached manual directories. The fetcher refuses
to overwrite a manifest containing custom entries. Save your custom entries
separately, refresh official sources, then merge them back and re-ingest.

Kokkos core docs and Kernels release docs (requires Git and internet):

```sh
uv run fetch_kokkos.py          # reproduce the pinned sources
uv run fetch_kokkos.py --latest # newest core docs and latest stable Kernels
uv run ingest.py
```

NWS-HPC standards and JEDI docs (requires Git and internet):

```sh
uv run fetch_standards.py          # reproduce the pinned sources
uv run fetch_standards.py --ccpp-repo /path/to/ccpp-doc
uv run fetch_standards.py --latest # newest NWS release tag, current JEDI develop and current CCPP main
uv run ingest.py
```

`--latest` records the new commits/version labels in the lock file; it never
happens automatically.
Ingestion rebuilds SQLite in a transaction: failed imports preserve the previous
index. Empty sources and wrong-version entries are rejected. Stable IDs depend
on source name, title, location and content; re-search after a rebuild changes IDs.
There is no automatic folder watcher.

## Validation and limits

```sh
uv run python -m unittest discover -s tests -t .
uv run python -m tests.smoke_mcp
uv run python -m unittest tests.smoke_docker   # requires: docker build -t omd-mcp .
```

Tests cover section/subsection boundaries, module-qualified/nested routines,
source context, full-text pagination, version/source-kind filtering, stable IDs,
invalid requests and rollback. Regression tests against the actual bundled
manuals check signatures, arguments, overload discovery and release URLs for
NUOPC_CompSpecialize, NUOPC_DriverAddComp and NUOPC_Advertise. Real example searches
check driver registration and cap labels against the pinned source commit, and
regression coverage now pins prototype discoverability plus CCPP included-code
and auxiliary-file handling.
Further tests cover collection/version isolation across all seven libraries,
Markdown and RST parsing, included-code retrieval, fetcher helpers, and real
documentation from the Kokkos, NWS, JEDI and CCPP collections (32 unit tests total).
The smoke test exercises all twelve tools through a real MCP stdio client/server;
`tests.smoke_docker` replays the same calls inside the built image.

This validates retrieval, **not ESMF compilation, MPI execution, scientific
correctness, or an improvement in agent-generated code**. Those need evaluation
with your application and tests. The parser is a conservative routine scanner,
not a Fortran compiler: unusual prefixes, fixed-form syntax, bare END statements,
preprocessor branches and includes may need the full-file record. It does not
expand includes or infer a call graph. Manual diagrams and image-rendered
formulas are not extracted; consult the original linked pages when needed. No lifecycle rules are invented or hardcoded
as API facts; lifecycle references are retrieved from manuals.

All indexed text is stored locally. Tools are read-only and do not compile code,
run tests, edit your repository or access the network. Copilot performs those
programming actions in your workspace, under its normal controls. Your source
and index may contain confidential code; keep them protected accordingly.

## Sources

- [ESMF release documentation](https://earthsystemmodeling.org/static/releases.html)
- [8.9.1 NUOPC reference](https://earthsystemmodeling.org/docs/release/ESMF_8_9_1/NUOPC_refdoc/)
- [8.9.1 Building a NUOPC Model](https://earthsystemmodeling.org/docs/release/ESMF_8_9_1/NUOPC_howtodoc/)
- [8.9.1 Fortran reference](https://earthsystemmodeling.org/docs/release/ESMF_8_9_1/ESMF_refdoc/)
- [Pinned ESMF source](https://github.com/esmf-org/esmf/tree/bd03a249df907464fdad91b7c43985dedbc472c7)
- [VS Code MCP configuration](https://code.visualstudio.com/docs/agents/reference/mcp-configuration)

- [Kokkos releases](https://github.com/kokkos/kokkos/releases)
- [Kokkos documentation](https://kokkos.org/kokkos-core-wiki/)
- [Kokkos Kernels releases](https://github.com/kokkos/kokkos-kernels/releases)
- [Kokkos Kernels documentation](https://kokkos.org/kokkos-kernels/docs/)
- [NWS HPC standards](https://nws-hpc-standards.readthedocs.io/en/stable/) — [source](https://github.com/NCO-HPC/nws-hpc-standards)
- [JEDI documentation](https://jcsda-jedi-docs.readthedocs-hosted.com/en/latest/) — [source](https://github.com/JCSDA/jedi-docs)
- [CCPP documentation](https://ccpp-doc.readthedocs.io/en/latest/) — [source](https://github.com/NCAR/ccpp-doc)
- [CCPP-SCM documentation](https://ccpp-scm.readthedocs.io/en/latest/) — [source](https://github.com/NCAR/ccpp-scm)
- [NUOPC application prototypes](https://github.com/esmf-org/nuopc-app-prototypes/tree/patch/8.9.1)
