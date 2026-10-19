# RDHPCS and OpenMP Documentation Collections

## Goal

Add three documentation collections to the OMD index, covering the user
requests for `https://docs.rdhpcs.noaa.gov`, the OpenMP 6.0 Examples
document, and the OpenMP 6.0 API Syntax Reference Guide:

- `rdhpcs` — NOAA RDHPCS user documentation (accounts, connecting, systems,
  SLURM, software, queue policy, FAQ).
- `openmp-examples` — the OpenMP 6.0 examples document as LaTeX prose plus
  its compilable example programs.
- `openmp-refguide` — the OpenMP 6.0 API Syntax Reference Guide, which
  exists only as a PDF.

This introduces the first PDF ingestion path to the server.

## Provenance decisions (verified 2026-10-19)

| Library | Version label | Source | Provenance basis |
| --- | --- | --- | --- |
| `rdhpcs` | `snapshot-9e584961345b` | `NOAA-RDHPCS/noaa-rdhpcs.github.io` @ `main` (`9e584961345b317cbc22c9de3c447371dbdee7c7`), `source/` tree (47 `.rst`, 1 `.md`) | The repository is the authoritative Sphinx source of the live site (`.readthedocs.yaml` builds `source/conf.py`); no tags or releases exist upstream, so the label is a commit snapshot, never a release claim |
| `openmp-examples` | `6.0.1` | `OpenMP/Examples` @ lightweight tag `v6.0.1` (`e22ea85883a09d9da4150f1f7142c4781caba3fd`) | Official tagged release of the examples document source; `v6.0.1` is the errata revision of the 6.0 document whose PDF the user linked (`v6.0` = `4c3de66d644e`) |
| `openmp-refguide` | `6.0` | Bundled `corpus/openmp-refguide/OpenMP-RefGuide-6.0-OMP60SC24-web.pdf` (1,450,649 bytes; SHA-256 `f2a157321d2a6a8fc11d35526346aca7840b4e5cf3d1a6ea18ead2a0c382c5a0`) | Official openmp.org publication, © 2024 OpenMP ARB, product code OMPSC24; the checksum is the pin because the URL has no versioned immutable home |

Licensing and attribution:

- RDHPCS: repository `LICENSE` is CC0-1.0; retained beside the corpus.
- `OpenMP/Examples`: no `LICENSE`/`COPYING` file, but `omp_copyright.txt`
  (OpenMP ARB, 1997-2025, BSD-style permission with disclaimer) is retained
  beside the corpus.
- Reference guide: no separate license text ships with the PDF. A
  `corpus/openmp-refguide/NOTICE.txt` records the copyright line printed in
  the document ("© 2024 OpenMP ARB OMPSC24"), the upstream URL, and the
  SHA-256. The catalog entry points at the PDF file itself, so the notice
  is retained beside the corpus without being indexed (see Ingestion).

## Architecture

### Acquisition

`rdhpcs` and `openmp-examples` join `fetch_weather.SNAPSHOT` as ordinary
git-snapshot entries, reusing the existing shallow-checkout, pinned-commit
verification, dirty-checkout refusal, license retention, catalog rewrite,
and `weather-lock.json` machinery. The module docstring is reworded to
"weather, workflow and HPC documentation snapshots" — the file already
holds non-weather tools (dask, ecFlow, grib2io).

- `rdhpcs`: `repo='NOAA-RDHPCS/noaa-rdhpcs.github.io'`, `ref='main'`,
  `doc_dir='source'`, `exts=('.rst','.md','.txt')`, `licenses=['LICENSE']`,
  version `snapshot-9e584961345b` (rolling; `--latest` re-resolves the
  branch tip). Asset directories (`_static`, `_templates`, `images`,
  `files`, `_downloads`, `_search`, `_templates_github`) are skipped by the
  existing `skip_dirs` behavior in `copy_docs`.
- `openmp-examples`: `repo='OpenMP/Examples'`, `ref='v6.0.1'`,
  `doc_dir='.'`, `exts=('.tex','.md','.txt')` for documentation, plus an
  `examples` entry with `doc_dir='.'` and code extensions
  `('.c','.f90','.f','.cpp','.h','.hpp')` — `copy_docs` recurses the whole
  tree, which captures every `<topic>/sources/` program (the `Chap_*.tex`
  chapters `\input` those topic directories) with relative paths preserved
  for citations. `TAG_VERSION['openmp-examples']` strips the leading `v`
  (`v6.0.1` -> `6.0.1`). `licenses=['omp_copyright.txt']`.
  `figs/` PDF/TikZ figures are not indexed (no matching extension).

The `copy_docs` helper's extension filter must also accept the example
code extensions; it already filters by suffix tuple, so the examples entry
passes its own tuple (same pattern as `fv3`'s `examples` config).

`openmp-refguide` is **catalog-only and tracked in git**: no fetcher entry.
`corpus.catalog.json` gains a source entry whose `path` is the PDF file
itself — `corpus/openmp-refguide/OpenMP-RefGuide-6.0-OMP60SC24-web.pdf`
(`build()` accepts a single-file path) — with an added `sha256` field. This
keeps the sibling `NOTICE.txt` out of the index: `.txt` is an accepted
suffix, so pointing the entry at the directory would index the notice as a
documentation unit. `fetch_weather.py` never rewrites or removes this entry
(its preserve-and-replace logic only touches entries whose `library` is in
its own managed set).

### Ingestion (`knowledge.py`)

1. `LIBRARIES` gains `'rdhpcs'`, `'openmp-examples'`, `'openmp-refguide'`.
2. `.pdf` joins the accepted suffix tuple in `build()`. Dispatch happens
   **before** `read_text` (PDFs are binary and would fail strict UTF-8):
   a `.pdf` file routes to the new `pdf_sections(path, source, url)`.
3. `pdf_sections` composes three testable pieces:
   - **Page text**: `pypdf.PdfReader(path).pages[i].extract_text()`, then
     strip running headers/footers by pattern (`OpenMP API 6.0 Page N`,
     `© 2024 OpenMP ARB …`, `www.openmp.org`, `CHAPTER <name> <n>`).
   - **Outline walk**: flatten `reader.outline` recursively, keeping depth
     for parent/ordinal nesting. Destination page numbers are unusable in
     this PDF (all bookmarks resolve to page 0), so anchoring is
     **title-based**: walk the outline in document order and locate each
     title in the stripped page text via whitespace-collapsed,
     case-folded, prefix-tolerant line matching, with a cursor that moves
     forward and a global fallback pass. Validated on the real file:
     65/67 anchored.
   - **Unmatched headings** (the two known back-matter entries "Become an
     OpenMP ARB Member" and "Index" collide with footer/TOC dot-leader
     noise): merge into the preceding section and append a per-file entry
     to `build()`'s existing `warnings` channel. No silent loss.
   - A PDF with **no outline** falls back to one whole-document unit,
     mirroring `html_sections`.
4. Unit metadata: `start_line`/`end_line` carry the 1-based PDF page span;
   `citation` is `library/version/name:p10-p11`; `url` is
   `…#page=10`. `kind` comes from the catalog entry as usual.
5. `build()` verifies the catalog `sha256` before indexing a file that
   carries one and raises on mismatch, failing the whole ingest (existing
   rollback preserves the prior database). This makes the tracked binary
   as trustworthy as a pinned commit.
6. `markup_sections` LaTeX branch gains `\cchapter` and `\bchapter` at
   level 1 (verified in the repository's `openmp.sty`: `\cchapter{title}{dir}`
   expands to `\chapter{title}` plus an example-directory side effect).
   No `\input` expansion: each `.tex` file indexes independently, like
   FV3/MPAS today.
7. Dependency: `pypdf>=5.4,<7` (BSD-3) added to `pyproject.toml` and
   `uv.lock`. Imported lazily inside the page-text helper so the runtime
   container — which only reads SQLite — never touches it unless a PDF is
   ingested at build time. PyMuPDF was rejected on AGPL grounds.

### MCP surface (13 -> 15 tools)

- `search_docs`/`search_code` docstring library lists gain the three
  labels.
- `get_rdhpcs_context(query, limit=4)`: NWS-style single-collection tool.
  Workflow notes: fetch full sections with `get_section`; queue-policy
  "must" statements are site policy, not API requirements; cite the page
  URL; the collection is a rolling `main` snapshot and system pages change
  without version bumps.
- `get_openmp_context(query, library='both', limit=4)`: Kokkos-style split
  tool returning `openmp-examples` and `openmp-refguide` result lists
  separately (the reference guide is terse clause syntax; the examples book
  is prose plus compilable code; mixing rankings dilutes both). Note field
  states that **neither collection is the normative OpenMP specification**
  — verify clause semantics against the compiler actually installed.
- Server `instructions` gains one sentence routing RDHPCS operations
  questions and OpenMP directive/clause questions to the new tools.

### Known limitations (recorded in README and tool notes)

- Multi-column PDF layout: dense reference-guide pages can interleave
  lines during extraction; code blocks keep their `S-n` line markers.
- Title-based anchoring is fragile to a reissued PDF; the SHA-256 pin
  converts that fragility into a loud ingest failure rather than silent
  drift.
- RDHPCS pages that are pure `.. toctree::` stubs (e.g. `systems/index.rst`)
  index as short parent units; content lives in the child pages, which the
  parent/child `get_section(include_subsections=True)` traversal handles.
- `OpenMP/Examples` example programs are labeled `kind=example` from the
  tagged release tree; they are upstream release examples, not compiled or
  tested by this project (same disclaimer as the ESMF release examples).

## Validation

- New `tests/test_pdf.py`: anchor matcher on synthetic page lists + outline
  (exact match, prefix-tolerant, cursor advance, global fallback,
  unanchored merge into preceding section, empty-outline whole-document
  fallback, header/footer stripping); `sha256` verification failure aborts
  `build()`; `.pdf` never reaches `read_text`.
- `tests/test_knowledge.py`: `\cchapter`/`\bchapter` produce level-1
  boundaries with the title from the first brace group; existing LaTeX
  levels unaffected.
- `tests/test_collections.py`: synthetic manifest + library-isolation loop
  gain `rdhpcs`, `openmp-examples`, `openmp-refguide`.
- `tests/test_fetch_weather.py`: `SNAPSHOT` pin coverage includes both new
  libraries; `tag_version('openmp-examples','v6.0.1')=='6.0.1'`; `rdhpcs`
  carries the rolling `snapshot-` label and `LICENSE`; the OpenMP entry
  retains `omp_copyright.txt` and defines an `examples` copy config.
- Live index build: run `fetch_weather.py --only rdhpcs,openmp-examples`,
  download the pinned refguide PDF once, run `ingest.py`, then pin exact
  unit counts into the shared-regression-index count test (expect ~48
  RDHPCS markup files, ~137 tex + ~609 code files, ~65 PDF units).
- `tests/smoke_mcp.py`: fifteen-tool line; `get_rdhpcs_context` and
  `get_openmp_context` return `collections` dicts on the synthetic corpus.
- `tests/smoke_docker.py`: after image rebuild, assert
  `search_docs(library='rdhpcs')` finds a known section (e.g. "lifespan"
  or "Gaea"), `get_openmp_context` returns both non-empty collection lists,
  and `list_collections` rows include the three new (library, version)
  pairs.
- Full suite (`unittest discover -s tests -t .`) passes before each commit;
  measure the shared regression index rebuild-time growth and record it.

## Rollout order

1. Fetch + commit `corpus/rdhpcs` and `corpus/openmp-examples`; add the
   tracked PDF + `NOTICE.txt` under `corpus/openmp-refguide/`.
2. Add `pypdf` to `pyproject.toml`, re-lock `uv.lock`.
3. `knowledge.py` changes (LIBRARIES, pdf_sections, sha256 check, LaTeX
   macros) with unit tests.
4. Catalog entries + live ingest + count pins.
5. `server.py` tools + instructions + smoke updates.
6. README (nineteen collections, three table rows, license paragraph,
   fifteen tools) and `.github/copilot-instructions.md` caveat paragraph.
7. Rebuild the `omd-mcp` image and run the docker smoke suite.

Push directly to `main` per repository convention.

## Out of scope

- The normative OpenMP 6.0 language specification itself (not free; no
  machine-readable source).
- Crawling `docs.rdhpcs.noaa.gov` rendered HTML (the git source is
  authoritative and already fits the snapshot pattern).
- OCR or geometry-aware reflow for multi-column pages.
- Automatic refresh of the pinned PDF (`--latest` does not touch
  catalog-only entries).
