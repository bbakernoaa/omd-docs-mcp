"""Smoke test the built Docker image over MCP stdio with a read-only rootfs.

Requires the image built by `docker build -t esmf-nuopc-mcp .`. Skips if the
image or docker CLI is unavailable so it never breaks a non-Docker checkout.
"""
import json
import shutil
import subprocess
import unittest

IMAGE = "esmf-nuopc-mcp"
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
        self.assertEqual(r["serverInfo"]["name"], "esmf-nuopc")

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