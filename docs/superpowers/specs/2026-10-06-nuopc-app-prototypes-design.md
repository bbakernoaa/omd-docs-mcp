# Design: NUOPC application prototypes and CCPP technical documentation

Date: 2026-10-06
Status: approved by user in brainstorming (prototypes: pin, file scope, fetcher
placement, kind; CCPP: `main` pin, label `ccpp`, two-entry included-code split,
`get_ccpp_context` tool, include despite absent license)

## Overview

This spec covers **two additions** to the omd server:

1. **NUOPC application prototypes** — the `esmf-org/nuopc-app-prototypes`
   repository folded in as a fourth managed source **inside the existing
   `esmf`/`8.9.1` collection** (`kind='example'`). Not a new library: it reuses
   `LIBRARIES`, `get_nuopc_context` and `search_code(kind='example')`, so the 51
   prototypes join the NUOPC evidence path alongside the two in-tree examples.
2. **CCPP technical documentation** — the `NCAR/ccpp-doc` repository added as a
   **new sixth library** (`ccpp`): a rolling `main`-branch snapshot with its own
   `get_ccpp_context` tool and a docs + included-code entry pair (the
   Kokkos-Kernels pattern). After this change the server has **six collections
   and eleven tools**.

| Attribute | Decision | Basis |
| --- | --- | --- |
| Repo | `https://github.com/esmf-org/nuopc-app-prototypes` | user request |
| Ref | branch `patch/8.9.1`, pinned commit `1645f4471da271e518213ceb574b0ada0ff3a169` | branch maintained for ESMF 8.9.1; matches the collection's version pin. Repo has **no** 8.9.1 tag (verified via `git ls-remote`), so a patch branch is the closest release-scoped ref. |
| Version label | `8.9.1` | `build()` enforces `library=='esmf' -> version==VERSION`; no new label style. |
| Kind | `example` | upstream curated examples; keeps `application` reserved for the user's own code. |
| Library | `esmf` (default; entry omits the key, matching existing ESMF entries) | "for the nuopc/esmf path" |
| Corpus path | `corpus/nuopc-app-prototypes/` | mirrors `corpus/examples` / `corpus/src` |
| Manifest name | `nuopc-app-prototypes` | distinct from `esmf/NUOPC/examples` so provenance is unambiguous |
| Fetcher | extend `fetch_corpus.py` | it already manages the esmf entries, guards, and the custom-entry refusal |

Measured at the pinned commit (shallow clone, 2026-10-06): 51 top-level
prototype directories, 355 tracked files, 9.3 MB. 196 `.F90`, 23 `.yaml`,
9 `.txt`, 6 `.md`, 6 `.config`, 53 `Makefile`, 44 `README` (no extension),
4 `.c`, 4 `.cfg`, 2 `.cmake`, 2 `.nc`, 1 each `.sh`/`.yml`/`.runconfig`/`.jl`,
1 `.gitignore`, 1 `nuopcExplorerScript`, 1 `testProtos.sh`. Under today's
whitelist, 288 files / 5.9 MB would index.

| Attribute (CCPP) | Decision | Basis |
| --- | --- | --- |
| Repo | `https://github.com/NCAR/ccpp-doc` | user request |
| Ref | branch `main`, pinned commit `a2f65334fda991fb7aa6a37716c003533529370e` (HEAD, 3 weeks old) | user explicitly chose `main` over the release tag |
| Version label | `snapshot-a2f65334fda9` | rolling snapshot; `conf.py release='6.0.0'` recorded as informational `target_release` only (JEDI treatment). `v6.0.0` (4 yr) and `v7.0.0` tags intentionally **not** indexed. |
| Library | `ccpp` (new 6th in `LIBRARIES`) | genuinely separate framework, not ESMF-scoped |
| Kind(s) | `documentation` (docs) + `example` (included-code) | mirrors `kokkos-kernels-docs` + `kokkos-kernels-includes` |
| Corpus paths | `corpus/ccpp/source`, `corpus/ccpp/included-code` | |
| Manifest names | `ccpp-docs`, `ccpp-included-code` | |
| Fetcher | extend `fetch_standards.py`; `standards-lock.json` gains `ccpp` | one home for RTD-style documentation collections |
| RTD | `https://ccpp-doc.readthedocs.io/en/latest/` (200, builds `main`); `/en/stable/` is 404 | provenance/citation URL |
| Tool | `get_ccpp_context(query, limit=4)` (11th) | convention: one context tool per non-esmf library |

Measured at the pinned `main` commit (shallow clone, 2026-10-06): 42 tracked
files; the Sphinx source lives in `CCPPtechnical/source/` — 15 `.rst`, 2 `.inc`
(`prolog.inc`, `ScientificDocRules.inc`), 2 `.txt` tree-layout files
(`ccpp_framework.txt`, `ccpp_physics.txt`), `conf.py`, `references.bib`,
`_templates/`, and `_static/` (PNG figures, `custom.css`, and the two
`literalinclude` targets `scheme_template.F90` / `scheme_template.meta`). The
docs entry copies `source/` **minus `_static/`** so the whitelist admits the
`.rst`/`.inc`/`.txt` content and skips `conf.py`/`.bib`/images automatically;
the two `_static` template files are copied separately into the included-code
entry. Both `literalinclude` references are in `CompliantPhysicsParams.rst`
(lines 99 and 365). The repo has **no license file and no license/disclaimer
text anywhere** (only `conf.py copyright = '2023'`); the collection is included
with that absence recorded, not fabricated.

## Goals

- Prototypes retrievable through the existing NUOPC path: `get_nuopc_context`
  (examples bucket), `search_code(kind='example', library='esmf')`,
  `get_routine` for whole files, `list_sources` showing the new source.
- Pinned, verified snapshot with the same guards as the ESMF checkout: exact
  commit match, clean tree, staged copy, refusal to clobber custom entries.
- Per-prototype `README` and run configuration files indexed, because they
  explain each design pattern (PetList, connector options, mediators, nesting,
  ESMX) that the code alone does not.
- CCPP technical documentation retrievable as a sixth library
  (`library='ccpp'`) via `get_ccpp_context`, `search_docs`/`get_section`, with
  the same isolation, pagination and provenance semantics as the other
  documentation collections.
- The two CCPP `literalinclude` targets (`scheme_template.F90`,
  `scheme_template.meta`) resolve through a separate `kind='example'` entry so
  `get_section` reports them as `included_code`, not `missing_included_code`
  (Kokkos Kernels precedent).
- Existing collections provably unchanged: identical unit counts and text for
  Kokkos, Kokkos Kernels, NWS and JEDI, and for the esmf manuals and `src`;
  only the esmf `example` count grows (prototypes) and `ccpp` is purely additive.
- Full delivery chain: fetch -> ingest -> commit corpus + index -> rebuild
  `omd-mcp` image -> all tests green -> push.

## Non-goals

- Prototypes: no new library label and no `get_prototypes_context` — they reuse
  the `esmf` collection and `get_nuopc_context`.
- Prototypes: no `develop`/HEAD content, no older `patch/*` or `release/*`
  branches, no feature branches.
- CCPP: branch `main` only — the `v6.0.0` and `v7.0.0` tags are intentionally
  not indexed (user chose the rolling branch). No new library beyond `ccpp`.
- No binary assets: the two prototype `.nc` mesh files and CCPP's `_static`
  PNG figures stay out of the index.
- No attempt to build or run the prototypes, or to build CCPP's Sphinx docs
  (prototypes need an ESMF install/`ESMFMKFILE`/MPI; CCPP needs Sphinx +
  sphinxcontrib-bibtex + LaTeX). Out of scope for a retrieval server.
- No certification that the prototypes compile against 8.9.1, or that the CCPP
  snapshot matches a tagged CCPP release — both are upstream branch code/docs.

## Component 1: `knowledge.py` ingest whitelist extension

Current filter (`build()`, line ~157) admits a fixed suffix set plus the exact
names `makefile` / `cmakelists.txt`. Extend the exact-name set with
`readme` and the suffix set with `.c`, `.config`, `.cfg`, `.cmake`, `.sh`,
`.runconfig`, `.jl` (prototypes) plus `.inc`, `.meta` (CCPP).

Verified blast radius: `find corpus -type f -name README -o -name '*.c' -o
-name '*.config' -o -name '*.cfg' -o -name '*.inc' -o -name '*.meta'` returns
**zero** files today, and no `.cmake`/`.sh`/`.runconfig`/`.jl` exists either.
The extension therefore changes nothing for existing sources; it only admits
prototype and CCPP files. `.nc` and image extensions are not added, so the
NetCDF meshes and PNG figures stay excluded by the whitelist (and would fail
`errors='strict'` decoding anyway).

Routing is unchanged: these are `kind='example'`, so every admitted file goes
through `code_units()`, which always emits a whole-file unit (title
`Full source file: <source>`) plus any Fortran routines it recognises. `.c`,
`.config`, `.cfg`, `README`, `.sh`, `.jl`, `.inc`, `.txt`, `.meta` therefore
land as complete-file records — the intended "full-file record" behaviour already documented in the
README for configurations and unrecognized source syntax. `.F90` files keep
their per-routine units with module context.

No schema change, no version-gate change, no search-behaviour change.

## Component 2: `fetch_corpus.py` prototypes support

- New module constants: `PROTOS_COMMIT='1645f4471da271e518213ceb574b0ada0ff3a169'`,
  `PROTOS_REF='patch/8.9.1'`,
  `PROTOS_URL='https://github.com/esmf-org/nuopc-app-prototypes'`.
- New CLI flag `--protos-repo PATH`: existing clean checkout at the pinned
  commit (same contract as `--esmf-repo`).
- Clone path (inside the existing `tempfile.TemporaryDirectory` staging area,
  so a failure leaves prior corpus/manifest/index intact) — a plain shallow
  clone of the whole tree (no sparse checkout; the repo is 9.3 MB):
  `git clone --depth 1 --branch patch/8.9.1 <url> <staging>/nuopc-app-prototypes`
  then verify `rev-parse HEAD == PROTOS_COMMIT` and refuse on a dirty tree.
  The branch tip is the pin; a future `--latest`-style refresh means updating
  the constant plus this spec, consistent with how ESMF's `COMMIT` works
  (no `--latest` flag is added here — `fetch_corpus.py` has never had one).
- Copy the working tree to `staging/nuopc-app-prototypes`, excluding `.git`
  only (whitelist filtering happens at ingest, exactly as for `src`/`examples`),
  and require the 51-directory tree to be non-empty (`if not any(...)`: raise).
- Swap into `corpus/nuopc-app-prototypes` in the same replacement loop as
  `manuals`/`examples`/`src`.
- Manifest entry appended to the esmf group:

```json
{
  "name": "nuopc-app-prototypes",
  "path": "corpus/nuopc-app-prototypes",
  "version": "8.9.1",
  "kind": "example",
  "url": "https://github.com/esmf-org/nuopc-app-prototypes/blob/1645f4471da271e518213ceb574b0ada0ff3a169",
  "revision": "1645f4471da271e518213ceb574b0ada0ff3a169",
  "managed": true,
  "version_basis": "patch/8.9.1 branch tip verified by commit; no 8.9.1 tag exists upstream"
}
```

  (No `library` key, matching the other eight esmf entries; `url` joins with the
  file's relative path at ingest to yield commit-specific blob links.)
- License handling: the repo has **no** LICENSE file (verified). Every source
  file carries the University of Illinois-NCSA header, the same license as ESMF
  itself, and `corpus/LICENSE` is already in the tree. The whole-tree copy
  already includes the repo's top-level `README.md` (ESMX recommendation and
  test-environment notes), which the whitelist indexes as a whole-file unit.
  Record the no-LICENSE-file fact in the README's provenance paragraph.
- The existing custom-entry guard already covers this: it inspects every
  `library=='esmf'` entry for `managed`, so a hand-added ESMF-scoped entry blocks
  a refresh rather than being silently dropped along with the new prototypes
  entry.

## Component 3: CCPP technical documentation collection (new library)

- `knowledge.py`: `LIBRARIES` grows to
  `('esmf','kokkos','kokkos-kernels','nws-hpc-standards','jedi','ccpp')`. There
  is no version gate for `ccpp` (only `esmf` is pinned to `VERSION`), so the
  `snapshot-*` label is accepted exactly as for Kokkos/JEDI. `build()` and
  `Knowledge.search()` already iterate `LIBRARIES`; no other logic change.
- `fetch_standards.py`: add a `ccpp` row to `DEFAULT` — repo `NCAR/ccpp-doc`,
  ref = pinned `main` commit, `branch: 'main'`, `version:
  'snapshot-a2f65334fda9'`, `doc_release: '6.0.0'` (informational), `rtd_url:
  'https://ccpp-doc.readthedocs.io/en/latest/'`. Reuse the existing clone /
  `rev-parse` / dirty-checkout guards, the staged temp-dir swap, and the lock
  write; `standards-lock.json` gains a `ccpp` key.

  CCPP breaks four assumptions the current code hardcodes for NWS/JEDI, so each
  moves into the per-library `DEFAULT` config (behaviour for `nws`/`jedi` stays
  byte-identical):
  1. **Docs directory.** `source=repo/'docs'` becomes `repo/config['doc_dir']`
     (`'docs'` for NWS/JEDI, `'CCPPtechnical/source'` for CCPP).
  2. **Copy filter.** `copy_markdown` gains an extension parameter; NWS/JEDI
     keep `('.rst','.md')`, CCPP uses `('.rst','.inc','.txt')` — which admits
     the two `.inc` and two `.txt` content files while `conf.py` and
     `references.bib` are excluded by extension. `_static` is added to the
     skip-parts set so PNG figures never reach the strict decoder.
  3. **Blob URL.** `url=f'.../blob/{commit}/docs'` uses `config['doc_dir']`.
  4. **License branch.** The `if jedi / else` block is replaced by a
     `license` policy in config: `jedi` requires a license file (existing
     `for/else raise`), `nws` snapshots the README `Disclaimer` section, `ccpp`
     has neither — no file copied, and its `version_basis` states "no license
     file in upstream repository". `read_doc_release` is generalised to
     `config['conf_path']` (`docs/conf.py` for JEDI,
     `CCPPtechnical/source/conf.py` for CCPP); NWS is unaffected.

  Per-library handling continues for the two extra CCPP pieces:
  - Included-code copy: `CCPPtechnical/source/_static/scheme_template.F90` and
    `_static/scheme_template.meta` → `corpus/ccpp/included-code`, listed in
    config as `included_code` paths (the `literalinclude` targets), matching the
    `kokkos-kernels-includes` shape. Refuse if a listed target is missing.
  - Two manifest entries: `ccpp-docs` (`kind: documentation`, carries
    `target_release: '6.0.0'` like `jedi`) and `ccpp-included-code`
    (`kind: example`), both `library: 'ccpp'`, `version:
    'snapshot-a2f65334fda9'`, commit-pinned `url`, `revision`, `managed: true`.
    The custom-entry guard already keys on `entry.get('library') in DEFAULT`,
    so both new names are protected automatically.
  - `--latest` refreshes `ccpp` to current `main` HEAD and rewrites the snapshot
    label + lock (the `else` branch already does `'snapshot-'+commit[:12]` for
    non-NWS libraries; `--ccpp-repo PATH` supplied-checkout override).
  - Module docstring and final print line mention CCPP; `--latest` help text
    covers three libraries.
- `server.py`: add `get_ccpp_context(query, limit=4)` mirroring
  `get_nws_context`/`get_jedi_context` — `if not 1<=limit<=8: raise`, return
  `{'collections': {'ccpp': knowledge.search(query,'documentation',limit,
  library='ccpp')}, 'workflow': [...], 'note': ...}` with four concrete
  workflow steps: (1) read the full section and its nested subsections before
  changing any CCPP scheme, host or suite code; (2) when a section lists
  `included_code` (the scheme templates), retrieve it with `get_routine` and
  follow it with `next_offset` until complete; (3) verify conventions against
  the CCPP framework and physics versions actually in the user's build, since
  this snapshot tracks `main`; (4) cite section URLs and RST line ranges. The
  note states this is a rolling `main` snapshot not certified to a tagged CCPP
  release and that the repo has no license file. Update the `search_docs`
  docstring to six libraries and the FastMCP instructions sentence. Eleven
  tools total.
- Included-code resolution needs **no** resolver change: `get_section` already
  scans `.. literalinclude::` refs in a section and matches the filename
  suffix against `kind='example'` units in the same `ccpp`/snapshot collection,
  returning `scheme_template.F90` / `scheme_template.meta` as `included_code`
  (readable via `get_routine`). Because the docs copy excludes `_static/`, the
  templates are indexed once (as examples), not duplicated.

## Component 4: tests

- `tests/test_release_corpus.py` (real index): assert a prototype routine is
  discoverable, e.g. `search_code('SetServices', 'example', library='esmf')`
  returns a hit whose `source` contains `nuopc-app-prototypes`, and that its
  provenance `revision` equals the pinned commit. Assert a per-prototype `README`
  and a `.config` file are retrievable as whole-file units (proving the whitelist
  extension works end to end).
- `tests/test_release_corpus.py` (real index): assert a CCPP doc section is
  discoverable via `search_docs('scheme', library='ccpp')`, and that
  `get_section` on the `CompliantPhysicsParams` page lists both
  `scheme_template.F90` and `scheme_template.meta` under `included_code` with
  **empty** `missing_included_code` (proves the two-entry split resolves the
  `literalinclude` refs). Assert a `.inc` and a `.txt` unit are retrievable.
- `tests/test_collections.py`: extend the synthetic per-library loop and the
  library-isolation loop to include `ccpp`.
- `tests/test_fetch_standards.py`: cover the CCPP docs-copy extension set
  (`.rst`/`.inc`/`.txt`, `_static/` excluded) and the two-file included-code
  copy.
- Isolation guard: after re-ingest, Kokkos/Kernels/NWS/JEDI still report exactly
  1610 / 641 / 22 / 1900 units and the esmf manuals/`src` counts are unchanged;
  only esmf `example` grows (prototypes) and `ccpp` is additive. Implement as a
  unit-count comparison over `(library, version, kind)` from
  `list_sources`-equivalent SQL, pinning every value except the two expected
  changes; record the measured `ccpp` total for the smoke test.
- Whitelist unit test: `build()` on a synthetic tree containing `README`,
  `x.config`, `x.c`, `x.inc`, `x.meta`, `x.nc` admits all but the `.nc`.
- `tests/smoke_docker.py`: update the `("esmf","8.9.1")` assertion to the new
  measured total (prototypes), add a `("ccpp","snapshot-a2f65334fda9")` count,
  add a `get_ccpp_context` request, and grow the tool-name/id sets 10→11.
- Existing suite + `tests/smoke_mcp.py` (now **eleven** tools, set grows by
  `get_ccpp_context`) must stay green.

## Component 5: docs and delivery

- `README.md`: the `esmf` row of the Collections table gains the 51 application
  prototypes; the provenance paragraph notes the patch-branch pin and the absent
  LICENSE file; the "Refreshing a collection" ESMF block notes the new source;
  the validation paragraph's test count updates.
- `README.md` (CCPP): Collections table grows to **six** rows (add `ccpp`) and
  the intro/unit-count sentence says six collections; a new `### CCPP`
  subsection (rolling `main` snapshot, `target_release` 6.0.0 informational,
  absent license, `get_ccpp_context`); the standards refresh block lists `ccpp`;
  the Sources section links the CCPP RTD and repo; the Tools table gains
  `get_ccpp_context` and "all ten tools" becomes "all eleven tools".
- `.github/copilot-instructions.md`: one sentence that release examples now
  include the 8.9.1-patched NUOPC application prototypes (51 patterns), still
  examples rather than API requirements; plus a CCPP line — call
  `get_ccpp_context` for CCPP physics-framework questions, verify against the
  CCPP version actually built (rolling `main` snapshot, no license file).
- Rebuild `omd-mcp` image and run `tests.smoke_docker` against it; commit
  `corpus/nuopc-app-prototypes/`, `corpus/ccpp/`, `corpus.json`,
  `standards-lock.json`, `data/nuopc.sqlite3`.

## Error handling

- Network or clone failure: staging temp dir is discarded; prior corpus,
  manifest and index untouched (existing behaviour).
- Commit mismatch or dirty tree: `ValueError`, no files written.
- Empty prototype tree: `ValueError` before swap.
- Manifest containing an unmanaged esmf entry: existing `parser.error` refusal;
  user must save custom entries separately.
- Binary `.nc`: excluded by the whitelist, so no decode error is reachable.
- CCPP has no license file: included by user decision with the absence recorded
  in `version_basis` and the README; no license text is fabricated.
- CCPP `conf.py`/`.bib`/images: excluded by the whitelist and the `_static/`
  copy rule, so they cannot reach the strict decoder.
- Ingest failure: existing transaction rollback preserves the prior index.

## Risks

1. **Patch-branch tip drift.** `patch/8.9.1` could receive new commits, making
   the pin stale rather than wrong. Mitigated by pinning the SHA (not the branch
   name) in code and manifest, and by the `rev-parse` guard.
2. **Index growth.** ~288 -> ~350 admitted files, est. +2,000 units and +6-10 MB
   on a 39 MB index. The 3.4 MB `CustomFieldDictionaryProto/fd.yaml` becomes one
   large whole-file unit; acceptable (search excerpts cap at 1,800 chars and
   `get_section`/`get_routine` paginate), and it is genuinely useful reference
   content.
3. **Whitelist broadening.** Admitting bare `README`/`.c`/`.config` is a global
   ingest change. Mitigated by the verified zero-hit blast radius on existing
   sources plus the isolation test.
4. **Retrieval noise.** 196 extra `.F90` files with many `SetServices` routines
   could swamp example results for generic queries. Mitigated by existing title
   weighting and by `limit`; the regression test pins discoverability rather than
   ranking.
5. **CCPP `main`-branch drift.** CCPP is pinned to a rolling branch, not a
   release; `--latest` moves the snapshot label. Mitigated by pinning the SHA
   (not the branch name) with a `rev-parse` guard, and by recording
   `target_release` only as metadata so the label never implies a release.
6. **CCPP absent license.** Unlike NWS (which shipped a disclaimer), `ccpp-doc`
   has no license or disclaimer text at all. Included per user with the gap
   documented in provenance; revisit if a redistribution policy is added.
