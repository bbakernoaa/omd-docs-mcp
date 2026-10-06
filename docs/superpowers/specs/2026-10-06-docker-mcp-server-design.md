# Docker-based MCP server — design

Date: 2026-10-06
Status: revised after review (see "Corrections")
Scope: run the `omd` MCP server as a local Docker image instead of `uv run server.py`.

## Goal

A machine with only Docker (no Python, no uv) can clone this repo, build the
image, and have GitHub Copilot use the ESMF/NUOPC + Kokkos tools through it.
"Clone and build" is only true if the index the image bakes is version
controlled — see `.gitignore` below.

Non-goals: publishing to a registry, image compression contests, replacing the
uv-based developer workflow, HTTP/SSE transport.

## Decisions taken

| Question | Decision |
| --- | --- |
| Why Docker? | No local Python/uv needed |
| Where does the SQLite DB come from? | Baked into the image, and **committed to git** so a clone can build |
| Relationship to uv config | Docker becomes the default in `.vscode/mcp.json` |
| Publishing | Never. Local `docker build` only |

## Corrections after review

The first draft of this spec contained two factual errors, both now verified:

- `uv.lock` **does** exist and is tracked. The draft rejected a lockfile-based
  build on the opposite premise. The build now installs pinned deps from it.
- `data/nuopc.sqlite3` is **not** tracked: `.gitignore` has `data/*` with
  `!data/.gitkeep`, and `git ls-files data/` returns only `.gitkeep`. So baking
  the host's DB into the image would not survive a fresh clone. `corpus/` (503
  files) *is* tracked, and `knowledge.build()` reads only local files, so a
  clone can re-index offline.

Given the choice between ingesting during the build, committing the index, or
requiring a host-side ingest first, the decision is to **commit the index**.
Accepted cost: a 31 MB derived binary in history that must be re-committed
after every `ingest.py` refresh. Mitigations: it is regenerable from `corpus/`
at any commit, and there is no CI or pre-commit hook in this repo to gate it
(`.github/` contains only `copilot-instructions.md`).

## Approaches considered

- **A. Single-stage slim image (chosen).** `python:3.12-slim`, dependencies
  installed from `uv.lock`, code and the committed DB copied in. Simplest
  reproducible build.
- **B. Multi-stage build (rejected).** Cleaner dep layer, but no size or
  security benefit worth the extra stage for a two-dependency stdio server.
- **C. Ingest inside the image (rejected by choice).** `RUN python ingest.py`
  from the tracked `corpus/` would keep the 31 MB blob out of git and stay
  build-reproducible; it was declined in favour of committing the index, which
  makes builds fast and the image byte-comparable to the host index.

## Architecture

```
Copilot Agent ──stdio──> docker run -i --rm --read-only omd-mcp
                              └── python server.py
                                    └── Knowledge("/app/data/nuopc.sqlite3")  # mode=ro
```

The container is a self-contained, read-only, stdio MCP server. The host needs
Docker only. `uv sync` / `uv run ingest.py` remain the documented developer path.

## Components

### `.gitignore` (modified)

Un-ignore the index so a clone can build the image:

```gitignore
data/*
!data/.gitkeep
!data/nuopc.sqlite3
```

### `Dockerfile` (new)

- Base: `python:3.12-slim` (satisfies `requires-python = ">=3.11"`).
- Install `uv`, then `uv sync --frozen --no-install-project` from `pyproject.toml`
  + `uv.lock`. `--frozen` fails the build if the lock is out of date with the
  manifest, and `--no-install-project` skips building the local package, which
  only needs to be importable as `server.py`/`knowledge.py`. The image then
  carries exactly the host's pinned resolutions — no drift between the two paths.
- `ENV UV_PROJECT_ENVIRONMENT=/usr/local` so the venv lands on the interpreter
  the `python` entrypoint already uses, instead of a second `/app/.venv` to keep
  on `PATH`.
- `WORKDIR /app`; copy `server.py`, `knowledge.py`, `data/nuopc.sqlite3`.
- Create an unprivileged user and run as it.
- `ENV DOCS_MCP_DB=/app/data/nuopc.sqlite3` (already the default via `ROOT`, but
  explicit so a bind-mount override is obvious).
- `ENTRYPOINT ["python", "server.py"]` — stdio transport, as today.

Layer order puts dependencies first and `data/nuopc.sqlite3` last, so a code
change does not re-resolve deps and a dep change does not re-copy 31 MB.

### `.dockerignore` (new)

Exclude everything the image does not need: `corpus/`, `docs/`, `tests/`,
`.git/`, `.github/`, `.vscode/`, `*.egg-info/`, `__pycache__/`,
`*.md`, `fetch_*.py`, `ingest.py`, `corpus.example.json`, `kokkos-lock.json`,
`data/.gitkeep`. The build context then carries four files — `pyproject.toml`,
`uv.lock`, `server.py`, `knowledge.py` — plus the index.

`corpus/` is excluded deliberately: the server reads only the SQLite index, and
re-indexing is a host-side job (`uv run ingest.py`), which needs the fetch
scripts and network that are also excluded.

### `.vscode/mcp.json` (modified)

```json
{
  "servers": {
    "omd": {
      "type": "stdio",
      "command": "docker",
      "args": ["run", "-i", "--rm", "--read-only",
               "--memory=512m", "omd-mcp"]
    }
  }
}
```

`-i` is required: an MCP stdio server only works with stdin attached.
`--rm` avoids accumulating containers. `--read-only` is safe because
`Knowledge.connect()` opens SQLite with `mode=ro` (`knowledge.py:187`), so the
server never writes; it matches the `readOnlyHint` on every tool.

### `README.md` (modified)

Add a "Run with Docker" section: build once with `docker build -t omd-mcp .`,
then enable the server from `MCP: List Servers`. Keep the uv instructions as the
developer path.

State the refresh procedure as one chain, since the index is now a committed
artifact: `fetch_corpus.py` / `fetch_kokkos.py` → `ingest.py` → `git add
data/nuopc.sqlite3` → `docker build`. Skipping the commit leaves the repo
history and the image pointing at different indexes; skipping the build leaves
the running container serving a stale index.

## Data flow

1. Copilot starts the server via `docker run -i --rm ...`.
2. `server.py` resolves the DB from `DOCS_MCP_DB`, defaulting to
   `/app/data/nuopc.sqlite3`.
3. Queries run against the baked FTS5 index; results return over stdout.

## Error handling

- Missing or corrupt baked DB → SQLite error at startup, surfaced in the VS Code
  MCP server output. No silent fallback to an empty index.
- Image not built → `docker: No such image` in the same output; the README build
  command is the fix.
- Stale index after a corpus refresh → not an error the container can detect;
  documented as a manual rebuild step.

## Testing

1. `docker build -t omd-mcp .` succeeds. The lockfile was resolved under
   host Python 3.14; the image uses 3.12, so the build must confirm
   `uv sync --frozen` accepts 3.12 rather than assuming it.
2. `docker run -i --rm --read-only omd-mcp` answers an MCP handshake over
   stdin: `initialize`, then `tools/list`, then a `list_collections` call returns
   the three collections with the counts verified above (2138 / 1610 / 641).
3. `--read-only` confirmed working: the container starts and serves queries with
   no writable filesystem.
4. Existing host path still works: `uv run python tests/smoke_mcp.py` prints
   "All eight MCP tools passed real stdio smoke test", unaffected by these
   changes.
5. `.gitignore` change verified: `git check-ignore -v data/nuopc.sqlite3` returns
   nothing, and `git ls-files data/` lists both `.gitkeep` and `nuopc.sqlite3`.

Report actual build/test output; do not claim validation that was not run. The
pinned-dependency and read-only-fs risks (steps involving the real index) were
already exercised natively during this review; the Docker-specific layers are
still unverified until implementation runs them.

## Assumptions

- Docker Desktop is present on the host (verified: server 29.7.2, buildx
  v0.36.1).
- `data/nuopc.sqlite3` is current: verified newer (09:03) than `corpus/` and
  `kokkos-lock.json` (09:02) after the latest fetch + ingest.
- This is a git repo (`main`, `a2b5e94`); the earlier "not a git repo" reading
  was a stale cwd result. The spec is therefore committed like any other change.
- Implementation must re-verify that `data/nuopc.sqlite3` is tracked after the
  `.gitignore` edit (`git check-ignore -v` returns nothing for it) before
  claiming the clone-and-build path works.
- `pyproject.toml` has **no** `readme` field, so the draft's "copy README.md for
  metadata" step is unnecessary.
- The image no longer needs `corpus/`. That was justified only as "the container
  can re-index if needed"; re-indexing also needs the fetch scripts and network,
  so it stays a documented host-side uv job. Dropping it saves 12 MB.
- `uv sync --frozen --no-install-project` was tested in a clean directory
  containing only `pyproject.toml` + `uv.lock`: resolves and installs the pinned
  set with no project source present. `uv export` also works but emits a 97-line
  requirements file with platform markers; `--frozen` avoids that extra artifact.
- The pinned set was then exercised end-to-end: `server.py` + `knowledge.py` +
  the real `data/nuopc.sqlite3` under that venv answered an MCP stdio handshake
  (`initialize` → `notifications/initialized` → `tools/call list_collections`)
  with `esmf 8.9.1` (2138 units), `kokkos snapshot-3cf2e0638b24` (1610) and
  `kokkos-kernels 5.2.2` (641).
- `PRAGMA journal_mode` on the shipped index is `delete`, not WAL, and there are
  no `-wal`/`-shm` side files. So `--read-only` rootfs is safe; with WAL the
  same flag would fail at first query.
