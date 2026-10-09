#!/usr/bin/env bash
# Launch the omd MCP server container, named "omd-mcp".
#
# The container is started detached with stdin held open (-d -i) so the
# stdio MCP server stays alive as a named service. Because --pull=never is
# used, the local-only image is never fetched from a registry.
#
# Usage:
#   ./run-omd-mcp.sh            # start (builds the image first if missing)
#   ./run-omd-mcp.sh --rebuild  # force docker build, then start
#   ./run-omd-mcp.sh --stop     # stop and remove the named container
#
# While it is running, connect a stdio session with:
#   docker exec -i omd-mcp python server.py
# (that reuses the named container instead of starting another one).
set -euo pipefail

IMAGE="omd-mcp"
NAME="omd-mcp"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

stop_container() {
  # Remove any container (running or stopped) already using the name so
  # `docker run --name` never fails with a conflict.
  if [ -n "$(docker ps -aq --filter "name=^${NAME}$")" ]; then
    docker rm -f "${NAME}" >/dev/null
    echo "Removed existing container '${NAME}'."
  fi
}

case "${1:-}" in
  --stop)
    stop_container
    echo "Container '${NAME}' stopped."
    exit 0
    ;;
  --rebuild)
    echo "Building image '${IMAGE}' from ${REPO_DIR} ..."
    docker build -t "${IMAGE}" "${REPO_DIR}"
    ;;
  "")
    :
    ;;
  *)
    echo "Unknown option: $1" >&2
    echo "Usage: $0 [--rebuild|--stop]" >&2
    exit 2
    ;;
esac

# Build only when the image is absent, so a normal launch stays fast.
if ! docker image inspect "${IMAGE}" >/dev/null 2>&1; then
  echo "Image '${IMAGE}' not found; building from ${REPO_DIR} ..."
  docker build -t "${IMAGE}" "${REPO_DIR}"
fi

stop_container

docker run -d -i --rm --read-only --pull=never --memory=512m \
  --name "${NAME}" "${IMAGE}" >/dev/null

echo "Started container '${NAME}' from image '${IMAGE}'."
docker ps --filter "name=^${NAME}$" \
  --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
