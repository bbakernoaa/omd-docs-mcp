# Read-only scientific documentation MCP server over stdio.
# Build:  docker build -t omd-mcp .
# Run:    docker run -i --rm --read-only --memory=512m omd-mcp
FROM python:3.12-slim AS build

# uv resolves the pinned dependency set from uv.lock.
RUN pip install --no-cache-dir uv

WORKDIR /app

# Dependency layer first: cached until pyproject.toml/uv.lock change.
COPY pyproject.toml uv.lock ./
ENV UV_PROJECT_ENVIRONMENT=/usr/local
RUN uv sync --frozen --no-install-project

# Build a fresh index from the catalog and bundled sources. PyTorch docs are
# fetched from their pinned version paths during this build.
COPY corpus.catalog.json build_manifest.py fetch_pytorch.py ingest.py knowledge.py ./
COPY corpus/ ./corpus/
RUN python fetch_pytorch.py && python ingest.py

FROM python:3.12-slim AS runtime
RUN pip install --no-cache-dir uv \
    && useradd --create-home --shell /usr/sbin/nologin appuser
WORKDIR /app
COPY pyproject.toml uv.lock ./
ENV UV_PROJECT_ENVIRONMENT=/usr/local
RUN uv sync --frozen --no-install-project
COPY --from=build --chown=appuser:appuser /app/data/nuopc.sqlite3 data/nuopc.sqlite3
COPY --chown=appuser:appuser server.py knowledge.py ./

# DOCS_MCP_DB is already the ROOT/data/nuopc.sqlite3 default in server.py;
# set it explicitly so a bind-mount override is obvious.
ENV DOCS_MCP_DB=/app/data/nuopc.sqlite3 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER appuser
ENTRYPOINT ["python", "server.py"]