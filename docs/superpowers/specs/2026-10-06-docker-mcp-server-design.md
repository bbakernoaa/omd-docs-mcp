# Docker-based MCP server — design

Date: 2026-10-06
Status: approved (pending spec review)
Scope: run the `esmf-nuopc` MCP server as a local Docker image instead of `uv run server.py`.

## Goal

A machine with only Docker (no Python, no uv) can clone this repo, build the
image, and have GitHub Copilot use the ESMF/NUOPC + Kokkos tools through it.

Non-goals: publishing to a registry, image compression contests, replacing the
uv-based developer workflow, HTTP/SSE transport.

## Decisions taken

| Question | Decision |
| --- | --- |
| Why Docker? | No local Python/uv needed |
| Where does the SQLite DB come from? | Baked into the image (copy `data/nuopc.sqlite3`) |
| Relationship to uv config | Docker becomes the default in `.vscode/mcp.json` |
| Publishing | Never. Local `docker build` only |

## Approaches considered

- **A. Single-stage slim image (chosen).** `python:3.12-slim` + the two runtime
  deps, code and baked DB copied in. Simplest reproducible build; no lockfile
  churn.
- **B. Multi-stage uv build (rejected).** Cleaner dep layer, but the repo has no
  `uv.lock`, so it adds lockfile maintenance for little gain.
- **C. Ingest inside the image (rejected).** `RUN python ingest.py` duplicates a
  31 MB artifact per build, slows builds, and couples them to the fetch step.
  The repo already ships an indexed DB.

## Architecture

```
Copilot Agent ──stdio──> docker run -i --rm --read-only esmf-nuopc-mcp
                              └── python server.py
                                    └── Knowledge("/app/data/nuopc.sqlite3")  # mode=ro
```

The container is a self-contained, read-only, stdio MCP server. The host needs
Docker only. `uv sync` / `uv run ingest.py` remain the documented developer path.

## Components

### `Dockerfile` (new)

- Base: `python:3.12-slim`.
- Install runtime deps directly (`mcp>=1.12,<2`, `beautifulsoup4>=4.12,<5`) with
  `pip install --no-cache-dir`; no editable install of the project, since only
  `server.py` and `knowledge.py` are needed at runtime.
- `WORKDIR /app`; copy `server.py`, `knowledge.py`, `corpus/`,
  `data/nuopc.sqlite3`, `pyproject.toml` (metadata only).
- Create an unprivileged user and run as it.
- `ENV DOCS_MCP_DB=/app/data/nuopc.sqlite3` (already the default via `ROOT`, but
  explicit so a bind-mount override is obvious).
- `ENTRYPOINT ["python", "server.py"]` — stdio transport, as today.

### `.dockerignore` (new)

Exclude `esmf_nuopc_mcp.egg-info/`, `tests/`, `.vscode/`, `.git/`,
`__pycache__/`, `*.md`, `fetch_*.py`, `kokkos-lock.json`,
`data/.gitkeep`, and `docs/`, so the build context stays lean and the image
contains only runtime files. `ingest.py` is kept (with `corpus/` and the
manifests) so the container can re-index if ever needed.

Note: `corpus/` is kept in the image even though the server never reads it at
runtime — it is small (12 MB), lets the container run `ingest.py` if ever needed,
and avoids a second "runtime only" file list to maintain.

### `.vscode/mcp.json` (modified)

```json
{
  "servers": {
    "esmf-nuopc": {
      "type": "stdio",
      "command": "docker",
      "args": ["run", "-i", "--rm", "--read-only",
               "--memory=512m", "esmf-nuopc-mcp"]
    }
  }
}
```

`-i` is required: an MCP stdio server only works with stdin attached.
`--rm` avoids accumulating containers. `--read-only` is safe because
`Knowledge.connect()` opens SQLite with `mode=ro` (`knowledge.py:187`), so the
server never writes; it matches the `readOnlyHint` on every tool.

### `README.md` (modified)

Add a "Run with Docker" section: build once with `docker build -t esmf-nuopc-mcp .`,
then enable the server from `MCP: List Servers`. State the rebuild trigger:
after any `fetch_corpus.py` / `fetch_kokkos.py` + `ingest.py` refresh, rebuild
the image, otherwise the baked index is stale. Keep the uv instructions as the
developer path.

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

1. `docker build -t esmf-nuopc-mcp .` succeeds.
2. `docker run -i --rm --read-only esmf-nuopc-mcp` answers an MCP handshake over
   stdin: `initialize`, then `tools/list`, then a `list_collections` call returns
   the expected `esmf` / `kokkos` / `kokkos-kernels` collections.
3. `--read-only` confirmed working: the container starts and serves queries with
   no writable filesystem.
4. Existing host path still works: `uv run python tests/smoke_mcp.py` (or the
   equivalent current test) unaffected by these changes.

Report actual build/test output; do not claim validation that was not run.

## Assumptions

- Docker Desktop is present on the host (verified: server 29.7.2, buildx
  v0.36.1).
- `data/nuopc.sqlite3` is current: verified newer (09:03) than `corpus/` and
  `kokkos-lock.json` (09:02) after the latest fetch + ingest.
- This directory is not a git repo (`git status` → fatal), so the spec is saved
  but not committed; the commit step of the brainstorming workflow does not
  apply here.
