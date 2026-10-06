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