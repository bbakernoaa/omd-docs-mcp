# Docker MCP Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the `omd` MCP server as a locally-built Docker image (stdio transport, read-only container) so a machine with only Docker — no Python, no uv — can clone, build, and use it.

**Architecture:** A single-stage `python:3.12-slim` image installs the project's pinned dependencies with `uv sync --frozen --no-install-project`, copies `server.py` + `knowledge.py` + the committed SQLite index, and runs `python server.py` over stdio as an unprivileged user. `.vscode/mcp.json` launches it via `docker run -i --rm --read-only`.

**Tech Stack:** Docker (buildx), Python 3.12, uv, FastMCP, SQLite FTS5.

## Global Constraints

- Target runtime is ESMF 8.9.1; the server is read-only and must never write to its database.
- Python floor: `requires-python = ">=3.11"` (`pyproject.toml`). Image base is `python:3.12-slim`.
- Dependencies are pinned via the tracked `uv.lock`; the image must install with `--frozen` so a lock/manifest mismatch fails the build.
- The image is built locally only. There is NO registry, NO `docker push`, NO published image.
- `data/nuopc.sqlite3` must be committed to git so a fresh clone can build the image (it is currently gitignored by `data/*`).
- The database is opened read-only (`knowledge.py:187`, `mode=ro`) and its `journal_mode` is `delete` (verified, no `-wal`/`-shm` side files), which is what makes `--read-only` rootfs safe.
- Tests run with `uv run python -m unittest discover -s tests -t .` (there is no pytest in the env) and the stdio smoke test `uv run python tests/smoke_mcp.py`.

## Verified facts (do not re-derive; re-confirm only if code changed)

- `uv sync --frozen --no-install-project` on `python:3.12-slim` builds successfully and imports `mcp` + `bs4` — the lock resolves under host Python 3.14 and is accepted on 3.12.
- A probe image built this way answers a full MCP stdio handshake (`initialize` → `notifications/initialized` → `tools/list` → `tools/call`) with `--read-only --memory=512m`.
- `list_collections` in-container returns the three collections: `esmf 8.9.1` (2138 units total: 1764 documentation / 18 example / 356 implementation), `kokkos snapshot-3cf2e0638b24` (1610), `kokkos-kernels 5.2.2` (641).
- `search_docs(query="NUOPC")` returns hits; `search_docs(query="gemm", library="kokkos-kernels")` returns `KokkosBlas::gemm`. `search_docs(query="NUOPC_CompInitialize")` returns ZERO hits on the real index — do NOT use it as an assertion.
- `get_nuopc_context(query="driver SetServices", focus="driver", limit=4)` returns 4 documentation, 3 lifecycle_references, 4 examples.
- Peak container RSS under a 9-call heavy workload is ~48 MiB. The `--memory=512m` cap has >10x headroom.
- Image size is ~82 MB (compressed layer sum); `uv` remains in the image (harmless).
- `pyproject.toml` has NO `readme` field, so README.md is not needed for metadata.

---

### Task 1: Commit the SQLite index so a clone can build

**Files:**
- Modify: `.gitignore` (the `data/*` / `!data/.gitkeep` block)

**Interfaces:**
- Consumes: nothing.
- Produces: `data/nuopc.sqlite3` present in a fresh `git clone`, which Tasks 2 and 4 COPY into the image.

- [ ] **Step 1: Edit `.gitignore`**

Find the block:
```gitignore
data/*
!data/.gitkeep
```
Replace with:
```gitignore
data/*
!data/.gitkeep
!data/nuopc.sqlite3
```

- [ ] **Step 2: Verify the index is no longer ignored**

Run: `git check-ignore -v data/nuopc.sqlite3`
Expected: NO output, exit code 1 (the file is not ignored). If it prints a matching rule, the edit is wrong.

Run: `git status --porcelain data/`
Expected: `?? data/nuopc.sqlite3`

- [ ] **Step 3: Confirm the index is current before committing it**

Run: `uv run ingest.py`
Expected: a JSON count summary printed, exit 0. This regenerates `data/nuopc.sqlite3` from the tracked `corpus/` so the committed artifact matches the source of truth.

- [ ] **Step 4: Stage and commit**

```bash
git add .gitignore data/nuopc.sqlite3
git commit -m "Track nuopc.sqlite3 index so the Docker image builds from a clone"
```

- [ ] **Step 5: Sanity-check the committed blob is readable**

Run: `git ls-files data/ && sqlite3 data/nuopc.sqlite3 'SELECT library,version,count(*) FROM units GROUP BY 1,2'`
Expected: `data/.gitkeep` and `data/nuopc.sqlite3` listed; three rows: `esmf|8.9.1|2138`, `kokkos|snapshot-3cf2e0638b24|1610`, `kokkos-kernels|5.2.2|641`.

---

### Task 2: Add the Dockerfile and .dockerignore

**Files:**
- Create: `Dockerfile`
- Create: `.dockerignore`

**Interfaces:**
- Consumes: `data/nuopc.sqlite3` (Task 1), `pyproject.toml`, `uv.lock`, `server.py`, `knowledge.py`.
- Produces: image tag `omd-mcp:latest` with entrypoint `python server.py`, DB at `/app/data/nuopc.sqlite3`. Task 3's `mcp.json` and Task 5's smoke test run against this tag.

- [ ] **Step 1: Create `.dockerignore`**

Write exactly this (the build context must exclude `corpus/`, `docs/`, `tests/`, `.git`, and the fetch/ingest tooling — the server reads only the index):
```
.git
.github
.gitignore
.dockerignore
Dockerfile
.venv
__pycache__/
*.pyc
.pytest_cache
docs
tests
corpus
corpus.json
corpus.example.json
fetch_corpus.py
fetch_kokkos.py
ingest.py
kokkos-lock.json
*.egg-info/
.vscode
README.md
data/.gitkeep
```

- [ ] **Step 2: Create `Dockerfile`**

```dockerfile
# Read-only ESMF/NUOPC + Kokkos MCP server over stdio.
# Build:  docker build -t omd-mcp .
# Run:    docker run -i --rm --read-only --memory=512m omd-mcp
FROM python:3.12-slim

# uv resolves the pinned dependency set from uv.lock.
RUN pip install --no-cache-dir uv

WORKDIR /app

# Dependency layer first: cached until pyproject.toml/uv.lock change.
COPY pyproject.toml uv.lock ./
ENV UV_PROJECT_ENVIRONMENT=/usr/local
RUN uv sync --frozen --no-install-project

# Drop privileges; app owns only the read-only runtime files.
RUN useradd --create-home --shell /usr/sbin/nologin appuser

# Application code + the committed index, copied last.
COPY --chown=appuser:appuser server.py knowledge.py ./
COPY --chown=appuser:appuser data/nuopc.sqlite3 data/

# DOCS_MCP_DB is already the ROOT/data/nuopc.sqlite3 default in server.py;
# set it explicitly so a bind-mount override is obvious.
ENV DOCS_MCP_DB=/app/data/nuopc.sqlite3 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER appuser
ENTRYPOINT ["python", "server.py"]
```

- [ ] **Step 3: Verify the build context is trimmed**

Run: `docker build --no-cache -t omd-mcp . 2>&1 | grep -i "transferring context\|load build context"`
Expected: a context size in the low tens of MB (code + lock + index), NOT ~43 MB (corpus excluded). If corpus/ or .git is transferred, `.dockerignore` is wrong.

- [ ] **Step 4: Build the image**

Run: `docker build -t omd-mcp .`
Expected: reaches `naming to docker.io/library/omd-mcp:latest` and `DONE`, exit 0. The `uv sync --frozen` step prints `+ mcp==1.30.0` and `+ beautifulsoup4==4.15.0`.

- [ ] **Step 5: Verify the entrypoint and user**

Run: `docker inspect omd-mcp --format '{{.Config.Entrypoint}} {{.Config.User}} {{.Config.Env}}'`
Expected: entrypoint `[python server.py]`, user `appuser`, env includes `DOCS_MCP_DB=/app/data/nuopc.sqlite3`.

- [ ] **Step 6: Commit**

```bash
git add Dockerfile .dockerignore
git commit -m "Add Dockerfile and .dockerignore for the omd MCP server"
```

---

### Task 3: Prove the container serves MCP over stdio (read-only)

**Files:**
- Test: `tests/smoke_docker.py`

**Interfaces:**
- Consumes: image `omd-mcp:latest` (Task 2).
- Produces: a repeatable container smoke test. No production code depends on it.

- [ ] **Step 1: Write the container smoke test**

Create `tests/smoke_docker.py`. It speaks the MCP handshake to `docker run -i --rm --read-only --memory=512m omd-mcp`, keeping stdin open until every expected response arrives (closing stdin early makes the server exit before processing the tail of the batch — this is the race that fakes "missing responses"). It asserts against the counts verified in the spec.

```python
"""Smoke test the built Docker image over MCP stdio with a read-only rootfs.

Requires the image built by `docker build -t omd-mcp .`. Skips if the
image or docker CLI is unavailable so it never breaks a non-Docker checkout.
"""
import json
import shutil
import subprocess
import unittest

IMAGE = "omd-mcp"
RUN = ["docker", "run", "-i", "--rm", "--read-only", "--memory=512m", IMAGE]

INIT = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                   "clientInfo": {"name": "smoke", "version": "0"}}}
NOTIF = {"jsonrpc": "2.0", "method": "notifications/initialized"}


def call(cid, name, arguments):
    return {"jsonrpc": "2.0", "id": cid, "method": "tools/call",
            "params": {"name": name, "arguments": arguments}}


REQUESTS = [
    INIT, NOTIF,
    {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    call(3, "list_collections", {}),
    call(4, "search_docs", {"query": "NUOPC", "limit": 6}),
    call(5, "get_nuopc_context", {"query": "driver SetServices", "focus": "driver", "limit": 4}),
    call(6, "search_docs", {"query": "gemm", "library": "kokkos-kernels", "limit": 6}),
]
EXPECTED_IDS = {1, 2, 3, 4, 5, 6}


def _payload(result):
    """Return structuredContent if present, else the JSON text content."""
    sc = result.get("structuredContent")
    if sc is not None:
        return sc
    for part in result.get("content", []):
        if part.get("type") == "text":
            try:
                return json.loads(part["text"])
            except json.JSONDecodeError:
                return part["text"]
    return None


class DockerMcpSmoke(unittest.TestCase):
    def setUp(self):
        if shutil.which("docker") is None:
            self.skipTest("docker CLI not available")

    def _exchange(self):
        proc = subprocess.Popen(
            RUN, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True)
        responses = {}
        try:
            for msg in REQUESTS:
                proc.stdin.write(json.dumps(msg) + "\n")
                proc.stdin.flush()
            # Read one response per request id; do NOT close stdin first.
            deadline_ids = set(EXPECTED_IDS)
            while deadline_ids:
                line = proc.stdout.readline()
                if not line:
                    self.fail(f"server closed stdout before answering ids {sorted(deadline_ids)}")
                if not line.startswith("{"):
                    continue
                j = json.loads(line)
                if j.get("id") in deadline_ids:
                    responses[j["id"]] = j
                    deadline_ids.discard(j["id"])
        finally:
            try:
                proc.stdin.close()
            except Exception:
                pass
            proc.terminate()
            proc.wait(timeout=10)
        return responses

    def test_initialize(self):
        r = self._exchange()[1]["result"]
        self.assertEqual(r["serverInfo"]["name"], "omd")

    def test_tools_list(self):
        tools = self._exchange()[2]["result"]["tools"]
        self.assertEqual({t["name"] for t in tools}, {
            "search_docs", "search_code", "get_section", "get_routine",
            "get_nuopc_context", "list_sources", "get_kokkos_context",
            "list_collections"})

    def test_list_collections(self):
        payload = _payload(self._exchange()[3]["result"])
        rows = payload if isinstance(payload, list) else payload.get("result", [])
        # list_collections returns one row per (library, version, kind);
        # sum units per (library, version) before comparing totals.
        units = {}
        for c in rows:
            key = (c["library"], c["version"])
            units[key] = units.get(key, 0) + c["units"]
        self.assertEqual(units.get(("esmf", "8.9.1")), 2138)
        self.assertEqual(units.get(("kokkos", "snapshot-3cf2e0638b24")), 1610)
        self.assertEqual(units.get(("kokkos-kernels", "5.2.2")), 641)

    def test_search_and_context(self):
        resp = self._exchange()
        docs = _payload(resp[4]["result"])
        docs = docs.get("result", docs) if isinstance(docs, dict) else docs
        self.assertTrue(docs, "search_docs('NUOPC') returned no hits")
        ctx = _payload(resp[5]["result"])
        self.assertEqual(ctx["version"], "8.9.1")
        self.assertTrue(ctx["documentation"])
        self.assertTrue(ctx["examples"])
        kok = _payload(resp[6]["result"])
        kok = kok.get("result", kok) if isinstance(kok, dict) else kok
        self.assertTrue(any("gemm" in (h.get("title", "").lower()) for h in kok))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the container smoke test**

Run: `uv run python -m unittest tests.smoke_docker -v`
Expected: all tests PASS. If the units assertions fail, print the raw `list_collections` payload first — the three totals (2138 / 1610 / 641) were verified against the index committed in Task 1, so a mismatch means the image baked a different index.

- [ ] **Step 3: Confirm it skips cleanly without the image**

Run: `docker rmi omd-mcp && uv run python -m unittest tests.smoke_docker 2>&1 | tail -5`
Expected: either SKIP (docker CLI missing) or a clear failure that the image is absent (`docker: No such image`). Rebuild with `docker build -t omd-mcp .` afterward. This documents that the test requires a prior build.

- [ ] **Step 4: Verify tests/ is not baked into the image**

The `.dockerignore` from Task 2 excludes `tests/`, so this new test file must not appear in `/app`.

Run: `docker run --rm --entrypoint ls omd-mcp /app`
Expected: only `data`, `knowledge.py`, `server.py` — no `tests/`.

- [ ] **Step 5: Commit**

```bash
git add tests/smoke_docker.py
git commit -m "Add read-only Docker MCP stdio smoke test"
```

---

### Task 4: Switch `.vscode/mcp.json` to the Docker command

**Files:**
- Modify: `.vscode/mcp.json`

**Interfaces:**
- Consumes: image `omd-mcp:latest` (Task 2).
- Produces: the editor-facing server definition. No code depends on it.

- [ ] **Step 1: Replace `mcp.json`**

```json
{
  "servers": {
    "omd": {
      "type": "stdio",
      "command": "docker",
      "args": ["run", "-i", "--rm", "--read-only", "--memory=512m", "omd-mcp"]
    }
  }
}
```

`-i` is required: an MCP stdio server only works with stdin attached. `--rm` avoids container accumulation. `--read-only` is safe because the index is opened `mode=ro` with `journal_mode=delete`.

- [ ] **Step 2: Verify the JSON parses**

Run: `python3 -c "import json;print(json.load(open('.vscode/mcp.json'))['servers']['omd']['command'])"`
Expected: `docker`

- [ ] **Step 3: Verify the configured args actually launch the server**

Run: `docker run -i --rm --read-only --memory=512m omd-mcp </dev/null >/dev/null 2>&1; echo exit=$?`
Expected: `exit=0` (server starts and exits cleanly on EOF).

- [ ] **Step 4: Commit**

```bash
git add .vscode/mcp.json
git commit -m "Run the omd MCP server through Docker by default"
```

---

### Task 5: Document the Docker path and the refresh chain

**Files:**
- Modify: `README.md` (the `## Quick start` section, ~line 94)

**Interfaces:**
- Consumes: `Dockerfile` (Task 2), `mcp.json` (Task 4).
- Produces: user-facing docs. No code depends on it.

- [ ] **Step 1: Insert a Docker quick start above the uv instructions**

Immediately after the `## Quick start` heading, before "Install Python 3.11+ and [uv]", insert the following text verbatim (the outer 4-backtick fence below is only this plan's wrapper — do NOT include it; the inserted README content starts at "With Docker only" and contains the inner ```sh fences as-is):

````markdown
With Docker only (no local Python or uv), build the image once from this
repository and Copilot runs the server in a read-only container:

```sh
docker build -t omd-mcp .
```

`.vscode/mcp.json` launches `docker run -i --rm --read-only --memory=512m
omd-mcp`. Enable it from `MCP: List Servers`. The image bundles the
committed `data/nuopc.sqlite3`, so a fresh clone plus Docker is enough.

**Refreshing the index.** The container serves the index baked at build time.
After any `fetch_corpus.py` / `fetch_kokkos.py` + `ingest.py` refresh, commit
`data/nuopc.sqlite3` and rebuild the image:

```sh
uv run ingest.py
git add data/nuopc.sqlite3 && git commit -m "Reindex"
docker build -t omd-mcp .
```

Skipping the rebuild leaves the running container on a stale index; the
container cannot detect this. The steps below use uv directly and remain the
developer path.
````

- [ ] **Step 2: Update the "Use in your actual model repository" block**

In that section's JSON example (search for `Merge the following into **your model's**`), replace the uv `command`/`args` with the Docker form so downstream repos copy the new default:

```json
{
  "servers": {
    "omd": {
      "type": "stdio",
      "command": "docker",
      "args": ["run", "-i", "--rm", "--read-only", "--memory=512m", "omd-mcp"]
    }
  }
}
```

Adjust the two sentences that follow the JSON block. Replace the current text beginning "Windows can use a path such as" with:

```markdown
The image must be built from this repository first (tag it on the target
machine with `docker build -t omd-mcp /absolute/path/to/docs-mcp`), then
any workspace can point `mcp.json` at the tag. `docker` must be on VS Code's
PATH; restart VS Code after installation. VS Code launches the stdio container;
there is no browser endpoint or separate manual server startup step. The uv
`command`/`args` form still works for developers who prefer a local Python env.
```

- [ ] **Step 3: Verify the README renders and the fenced blocks are balanced**

Run: `python3 -c "import re;t=open('README.md').read();print('fences',t.count(chr(96)*3));assert t.count(chr(96)*3)%2==0"`
Expected: an even fence count printed, no AssertionError. (The inserted block nests a fenced `sh` block inside the section; confirm the outer markdown is not broken by counting triple-backticks.)

- [ ] **Step 4: Full test suite still green on the host path**

Run: `uv run python -m unittest discover -s tests -t . && uv run python tests/smoke_mcp.py`
Expected: `Ran 19 tests ... OK` then `All eight MCP tools passed real stdio smoke test`.

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "Document Docker run path and index refresh chain"
```

---

### Task 6: End-to-end acceptance from a clean clone

**Files:**
- none (verification only)

**Interfaces:**
- Consumes: everything above.
- Produces: proof that the goal ("clone + Docker, no Python/uv") holds.

- [ ] **Step 1: Clone the repo to a scratch dir at the current HEAD**

```bash
rm -rf /tmp/docs-mcp-clone && git clone . /tmp/docs-mcp-clone
cd /tmp/docs-mcp-clone && ls data/nuopc.sqlite3
```
Expected: `data/nuopc.sqlite3` exists in the clone (proves Task 1 landed).

- [ ] **Step 2: Build from the clone**

Run: `docker build -t omd-mcp-clone .`
Expected: `DONE`, exit 0, image tagged.

- [ ] **Step 3: Serve a real tool call from the clone image, read-only**

```bash
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"p","version":"0"}}}\n{"jsonrpc":"2.0","method":"notifications/initialized"}\n{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"list_collections","arguments":{}}}\n' \
  | docker run -i --rm --read-only --memory=512m omd-mcp-clone 2>/dev/null | tail -1 | cut -c1-200
```
Expected: a JSON result naming `esmf` / `8.9.1`. This is the deliverable: a clone with only Docker builds and serves.

- [ ] **Step 4: Clean up scratch**

Run: `cd /Users/barry/Documents/docs-mcp && rm -rf /tmp/docs-mcp-clone && docker rmi omd-mcp-clone`
Expected: no errors.

- [ ] **Step 5: Record the acceptance result**

In the final report to the user, cite: the actual `docker build` output, the `list_collections` JSON from the clone, the `unittest`/`smoke_mcp` results from Task 5, and the `.gitignore`/`git ls-files` evidence from Task 1. Do not claim any of these ran unless the command output is in hand.
