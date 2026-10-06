# Design: NWS-HPC Standards and JEDI documentation collections

Date: 2026-10-06
Status: approved by user in brainstorming (scope, labels, tooling, fetch strategy, licensing)

## Overview

Add two documentation collections to the omd MCP server, following the established
Kokkos pattern (pinned GitHub source snapshot -> `corpus/` -> `corpus.json` ->
`ingest.py` -> committed SQLite index -> Docker image):

| Library label | Source | Version label | Provenance |
| --- | --- | --- | --- |
| `nws-hpc-standards` | `NCO-HPC/nws-hpc-standards` (NOAA/NWS HPC implementation standards; RTD `/en/stable/`) | `11.0.0` | Pinned tag `v11.0.0`; `docs/conf.py` declares `version = "11.0.0"`; RTD stable matches. Release-pinned basis. |
| `jedi` | `JCSDA/jedi-docs` (JEDI data assimilation docs; RTD `/en/latest/`) | `snapshot-<commit12>` | Rolling snapshot of `develop`, which is what RTD `/en/latest/` builds. `docs/conf.py` declares release `8.0.0`; recorded as metadata, **not** used as the collection label. Snapshot basis, not release-certified. |

Measured source sizes (2026-10-06): NWS `docs/` = 2 `.rst` (~88 KB tree). JEDI
`docs/` = 339 `.rst` + 4 `.md` (~2.07 MB of RST text; 305 `.rst` under
`inside/`). Neither repo uses `literalinclude` (verified: 0 occurrences), so no
included-code retrieval concerns. JEDI repo license: Apache-2.0 (`COPYING`).
NWS repo has **no license file** — only the DOC "as is" disclaimer in `README.md`;
user approved including it with the disclaimer text snapshotted alongside the corpus.

## Goals

- Both collections searchable via `search_docs`/`get_section`/`list_collections`
  with the same isolation, pagination, and provenance semantics as Kokkos.
- Two dedicated context tools (`get_nws_context`, `get_jedi_context`) mirroring
  `get_kokkos_context`'s bundle style. Server grows 8 -> 10 tools.
- A refreshable, pinned fetch script (`fetch_standards.py`) mirroring
  `fetch_kokkos.py` conventions (pinned revision, clean-checkout verification,
  `--latest`, refusal to clobber custom entries).
- Full delivery chain: fetch -> ingest -> commit corpus + index -> rebuild
  `omd-mcp` image -> all tests green.

## Non-goals

- No changes to ESMF/NUOPC or Kokkos retrieval behavior, phase semantics, or the
  `esmf`-scoped version pin.
- No HTML scraping of readthedocs.io — GitHub RST sources are the authoritative
  input (same decision as Kokkos core docs).
- No JEDI software source code, tutorials outside `docs/`, or the `jedi-edu`/`howto`
  directories.
- No cross-library search (default remains `library='esmf'`).

## Component 1: `fetch_standards.py` (new)

Mirrors `fetch_kokkos.py` structure and guards.

- `DEFAULT` config table:
  - `nws-hpc-standards`: repo `NCO-HPC/nws-hpc-standards`, ref `v11.0.0` (tag),
    `version: '11.0.0'`, docs dir `docs`.
  - `jedi`: repo `JCSDA/jedi-docs`, ref = pinned `develop` commit (recorded in
    `standards-lock.json`), `version: 'snapshot-<commit12>'`, docs dir `docs`,
    `doc_release: '8.0.0'` (from conf.py, informational).
- Clone procedure (identical guards to the Kokkos fetcher): `git init` +
  `remote add` + `fetch --depth 1 origin <ref>` + `checkout --detach FETCH_HEAD`;
  verify `rev-parse HEAD` equals the pinned commit (refuse on mismatch unless
  `--latest`); refuse on a dirty checkout (`status --porcelain`).
- Local-checkout overrides: `--nws-repo PATH` / `--jedi-repo PATH` (same contract
  as `--core-repo`/`--kernels-repo`: must be clean; with `--latest` must match
  the requested ref via `ls-remote`).
- `--latest`: NWS advances to the newest non-draft GitHub release tag (via
  `api.github.com/repos/.../releases/latest`, same as `latest_release()` in
  `fetch_kokkos.py`); JEDI advances to current `develop` HEAD with a new
  `snapshot-<commit12>` label. Never automatic.
- `standards-lock.json` is (re)written on **every** successful run with the
  current pins, commit shas, version labels, `doc_release` (JEDI), `rtd_url` and
  a `checked_at` timestamp — same behavior as `fetch_kokkos.py` writing
  `kokkos-lock.json` unconditionally.
- File selection into `corpus/<library>/source/` (staged in a temp dir under the
  repo root, then swapped, like the Kokkos fetcher): copy **only `.rst` and `.md`
  files**, preserving relative tree. This deliberately excludes `conf.py`,
  `Makefile`, `requirements.txt`, images, `venv/`, and `_build/`. (Verified on
  the pinned trees: JEDI `docs/venv/` contains only activation scripts with no
  ingest-allowlisted extensions, so exclusion is corpus hygiene; the ingest
  extension allowlist remains the second boundary.)
- License/provenance files copied **outside** the indexed `source/` path (same
  layout as `corpus/kokkos-kernels/LICENSE`): JEDI `COPYING` ->
  `corpus/jedi/COPYING`; NWS README disclaimer ->
  `corpus/nws-hpc-standards/DISCLAIMER.md` (the `## Disclaimer` section text of
  the repo README, snapshotted verbatim).
- Manifest handling: refuse if `corpus.json` contains non-managed entries for
  these two libraries ("Custom ... entries exist; preserve them separately");
  preserve all other entries (ESMF, Kokkos, application); write managed entries:

  ```json
  {
    "name": "nws-hpc-standards-docs",
    "path": "corpus/nws-hpc-standards/source",
    "library": "nws-hpc-standards",
    "version": "11.0.0",
    "kind": "documentation",
    "managed": true,
    "revision": "<commit sha>",
    "url": "https://github.com/NCO-HPC/nws-hpc-standards/blob/<commit>/docs",
    "version_basis": "Official release tag v11.0.0; matches RTD /en/stable/"
  }
  ```

  The JEDI entry uses `version_basis: "Rolling develop snapshot matching RTD
  /en/latest/; docs/conf.py declares release 8.0.0; not release-certified"` and
  `target_release: "8.0.0"`.
- `standards-lock.json` (new, repo root, analogous to `kokkos-lock.json`): per
  library the repo, ref/tag, commit, version label, `doc_release` (JEDI),
  `rtd_url`, and `checked_at` timestamp.

## Component 2: `knowledge.py` (edit)

- Introduce module constant
  `LIBRARIES = ('esmf', 'kokkos', 'kokkos-kernels', 'nws-hpc-standards', 'jedi')`.
- Replace the two inline whitelists with it:
  - `build()`: `if library not in LIBRARIES: raise ValueError('Unknown library')`
    (currently line ~148).
  - `Knowledge.search()`: same check (currently line ~195).
- No parser changes: `markup_sections()` already chunks `.rst`/`.md` by heading
  levels, and `.rst`/`.md` are already in the ingest extension allowlist. The
  exact-API heading regex (`NUOPC_|ESMF_|Kokkos*`) is a no-op for these
  libraries by design — NWS/JEDI headings are matched by ordinary FTS + BM25.
- `list_collections()` and `sources()` are data-driven over the DB and require no
  change.
- ESMF version pin (`library == 'esmf' and version != VERSION`) unchanged.

## Component 3: `server.py` (edit)

- Two new read-only tools, built like `get_kokkos_context`:

  ```python
  @mcp.tool(annotations=READ_ONLY)
  def get_nws_context(query: str, limit: int = 4) -> dict: ...
  @mcp.tool(annotations=READ_ONLY)
  def get_jedi_context(query: str, limit: int = 4) -> dict: ...
  ```

  Each validates `1 <= limit <= 8`, then returns
  `{'collections': {<library>: knowledge.search(query, 'documentation', limit, library=<library>)},
  'workflow': [...], 'note': ...}`.
- Workflow/note text per collection:
  - NWS: fetch full sections with `get_section` before asserting a standard;
    distinguish "must" requirements from examples/appendices; cite section URLs
    and line ranges; the index is a pinned `11.0.0` snapshot of a document that
    NCO updates.
  - JEDI: core docs are a rolling `develop` snapshot matching RTD `/en/latest/`;
    verify against the JEDI release actually installed/built; YAML examples in
    JEDI docs are configuration illustrations, not API guarantees.
- Update `search_docs` docstring: library list becomes
  `esmf, kokkos, kokkos-kernels, nws-hpc-standards, jedi`.
- Update the FastMCP `instructions` string: one added sentence directing agents to
  `get_nws_context`/`get_jedi_context` or `search_docs` with the correct library
  for NWS production standards or JEDI data assimilation questions.
- `get_nuopc_context`, `get_kokkos_context`, and all other tools unchanged.

## Component 4: tests (edit + add)

- `tests/smoke_mcp.py`: tool-name set assertion grows to the 10 names; final print
  says "All ten MCP tools passed"; add calls to `get_nws_context` and
  `get_jedi_context` with a representative query each (assert non-error,
  `collections` key present), plus one bad-library `search_docs` error check.
- `tests/smoke_docker.py`: after the real ingest, add summed-unit asserts for
  `('nws-hpc-standards', '11.0.0')` and `('jedi', 'snapshot-<commit12>')` using
  the measured counts, and update the embedded version string to the new JEDI
  snapshot label.
- `tests/test_collections.py`: extend the synthetic-manifest isolation loop with
  the two new libraries (synthetic `.rst` fixtures already exist); add real-corpus
  regression tests guarded by `skipUnless` on `standards-lock.json`, checking at
  minimum: NWS search finds the "Standard Environment Variables" table section
  with `version == '11.0.0'` and commit-bearing citation URL; JEDI search finds a
  known API/convention page (e.g. `FV3Jedi` or `GaugeObs` operator docs) with the
  snapshot label and `provenance.revision` in the URL.
- `tests/test_knowledge.py`: `test_invalid_requests`-style coverage — new library
  labels are accepted; an unknown label (e.g. `'bogus'`) still raises.
- `tests/test_release_corpus.py`: no change (ESMF-scoped).

## Component 5: delivery chain and docs

Run in order (the established refresh chain):

1. `uv run fetch_standards.py` (network; stages then swaps)
2. `uv run ingest.py` (rebuilds whole index from `corpus.json`)
3. Record measured unit counts; update `smoke_docker.py` asserts
4. `uv run python -m unittest discover -s tests` +
   `uv run python tests/smoke_mcp.py`
5. `git add corpus/nws-hpc-standards corpus/jedi standards-lock.json corpus.json
   data/nuopc.sqlite3` + code/test/doc changes (explicit paths; no `git add -A`)
6. `docker build -t omd-mcp .` then `uv run python -m unittest tests.smoke_docker`
7. README: new "Added NWS-HPC Standards and JEDI collections" section (collection
   table rows, version-label rationale, refresh commands incl. `--latest`,
   `standards-lock.json` note); Tools table gains the two context rows; Sources
   section gains RTD + GitHub links for both.
8. `.github/copilot-instructions.md`: brief paragraph — use `get_nws_context` for
   NWS production-standards questions, `get_jedi_context` for JEDI, verify labels
   from sources, JEDI snapshot caveat.

`.dockerignore` already excludes `corpus/` and `corpus*.json`; the image bakes
only `data/nuopc.sqlite3`, so **no Dockerfile change** is needed. Index growth
estimate: ~2.2 MB of new text -> roughly +2,500-4,000 documentation units and
~+10-15 MB of SQLite (FTS included); exact numbers recorded at ingest time.

## Error handling

- Fetcher: refuses on revision mismatch, dirty checkout, missing `docs/` dir, or
  custom entries for the target libraries; failures during staging leave the prior
  corpus and index intact (same staged-swap contract as `fetch_kokkos.py`).
- Ingest: unknown library -> `ValueError('Unknown library')`; the whole rebuild
  stays transactional (rollback preserves the previous index).
- Server: bad limit/library on the new tools -> `ValueError`; empty results are a
  normal empty list, not an error.
- Stale-container risk is unchanged and already documented: the container serves
  the build-time index; step 6 rebuild is mandatory after committing the index.

## Risks and open items

- JEDI `develop` moves frequently; the snapshot label pins exactly what was
  fetched. No silent drift: refresh is explicit (`--latest`) and re-recorded.
- NWS document is operational-policy text with tables rendered in RST; section
  chunking keeps each table with its heading (verified pattern from Kokkos RST
  handling). No formula/image extraction is expected — NWS appendices are tables
  and code blocks, both plain text.
- The NWS disclaimer is a US-government "as is" statement, not a copyright
  license; provenance is recorded in the corpus directory and README. If NCO
  later adds a formal license, the fetcher's license-file copy step picks up
  whatever files match at refresh time (extend the name list then).
- Committed index grows to ~40-45 MB (git history already carries 30.4 MB;
  user accepted the committed-index model previously).
