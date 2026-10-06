# Design: NUOPC application prototypes in the ESMF collection

Date: 2026-10-06
Status: approved by user in brainstorming (pin, file scope, fetcher placement, kind)

## Overview

Add the `esmf-org/nuopc-app-prototypes` repository as a **fourth managed source
inside the existing `esmf`/`8.9.1` collection**, classified `kind='example'`.
This is not a new library: `LIBRARIES`, `server.py`, `knowledge.py` search
isolation, the five collection labels, and all ten tools stay as they are. The
51 self-contained prototypes become part of the NUOPC evidence path so that
`get_nuopc_context` and `search_code(kind='example')` return real application
code alongside the two in-tree ESMF examples.

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

## Goals

- Prototypes retrievable through the existing NUOPC path: `get_nuopc_context`
  (examples bucket), `search_code(kind='example', library='esmf')`,
  `get_routine` for whole files, `list_sources` showing the new source.
- Pinned, verified snapshot with the same guards as the ESMF checkout: exact
  commit match, clean tree, staged copy, refusal to clobber custom entries.
- Per-prototype `README` and run configuration files indexed, because they
  explain each design pattern (PetList, connector options, mediators, nesting,
  ESMX) that the code alone does not.
- Existing collections provably unchanged: identical unit counts and text for
  esmf manuals/examples/src, Kokkos, Kokkos Kernels, NWS and JEDI.
- Full delivery chain: fetch -> ingest -> commit corpus + index -> rebuild
  `omd-mcp` image -> all tests green -> push.

## Non-goals

- No new library label, no new MCP tool, no `get_prototypes_context`.
- No `develop`/HEAD content, no older `patch/*` or `release/*` branches, no
  feature branches.
- No binary assets: the two `.nc` mesh files stay out of the index.
- No attempt to build or run the prototypes (they require an ESMF install,
  `ESMFMKFILE`, and MPI; out of scope for a retrieval server).
- No certification that the prototypes compile against 8.9.1 — they are
  upstream patch-branch code, tested by esmf-org, not by this project.

## Component 1: `knowledge.py` ingest whitelist extension

Current filter (`build()`, line ~157) admits a fixed suffix set plus the exact
names `makefile` / `cmakelists.txt`. Extend the exact-name set with
`readme` and the suffix set with `.c`, `.config`, `.cfg`, `.cmake`, `.sh`,
`.runconfig`, `.jl`.

Verified blast radius: `find corpus -type f -name README -o -name '*.c' -o
-name '*.config' -o -name '*.cfg'` returns **zero** files today, and no
`.cmake`/`.sh`/`.runconfig`/`.jl` exists either. The extension therefore changes
nothing for existing sources; it only admits prototype files. `.nc` is not
added, so the 1.5 MB of NetCDF stays excluded by the whitelist (and would fail
`errors='strict'` decoding anyway).

Routing is unchanged: these are `kind='example'`, so every admitted file goes
through `code_units()`, which always emits a whole-file unit (title
`Full source file: <source>`) plus any Fortran routines it recognises. `.c`,
`.config`, `.cfg`, `README`, `.sh`, `.jl` therefore land as complete-file
records — the intended "full-file record" behaviour already documented in the
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

## Component 3: tests

- `tests/test_release_corpus.py` (real index): assert a prototype routine is
  discoverable, e.g. `search_code('SetServices', 'example', library='esmf')`
  returns a hit whose `source` contains `nuopc-app-prototypes`, and that its
  provenance `revision` equals the pinned commit. Assert a per-prototype `README`
  and a `.config` file are retrievable as whole-file units (proving the whitelist
  extension works end to end).
- Isolation guard: after re-ingest, the four other collections still report
  exactly 1610 / 641 / 22 / 1900 units and the esmf **manual** counts are
  unchanged; only esmf `example` counts grow. Implement as a unit-count
  comparison over `(library, version, kind)` from `list_sources`-equivalent SQL,
  so the ESMF growth is expected and everything else is pinned.
- Whitelist unit test: `build()` on a synthetic tree containing `README`,
  `x.config`, `x.c`, `x.nc` admits the first three and skips the `.nc`.
- `tests/smoke_docker.py`: update the `("esmf","8.9.1")` assertion to the new
  measured total (single place; the other four stay).
- Existing suite (25 tests) + `tests/smoke_mcp.py` (ten tools, unchanged set)
  must stay green.

## Component 4: docs and delivery

- `README.md`: the `esmf` row of the Collections table gains the 51 application
  prototypes; the provenance paragraph notes the patch-branch pin and the absent
  LICENSE file; the "Refreshing a collection" ESMF block notes the new source;
  the validation paragraph's test count updates.
- `.github/copilot-instructions.md`: one sentence that release examples now
  include the 8.9.1-patched NUOPC application prototypes (51 patterns), still
  examples rather than API requirements.
- Rebuild `omd-mcp` image and run `tests.smoke_docker` against it; commit
  `corpus/nuopc-app-prototypes/`, `corpus.json`, `data/nuopc.sqlite3`.

## Error handling

- Network or clone failure: staging temp dir is discarded; prior corpus,
  manifest and index untouched (existing behaviour).
- Commit mismatch or dirty tree: `ValueError`, no files written.
- Empty prototype tree: `ValueError` before swap.
- Manifest containing an unmanaged esmf entry: existing `parser.error` refusal;
  user must save custom entries separately.
- Binary `.nc`: excluded by the whitelist, so no decode error is reachable.
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
