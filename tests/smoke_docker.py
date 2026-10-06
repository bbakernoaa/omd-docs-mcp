"""Smoke test the built Docker image over MCP stdio with a read-only rootfs.

Requires the image built by `docker build -t omd-mcp .`. Skips if the
image or docker CLI is unavailable so it never breaks a non-Docker checkout.
"""
import json
import queue
import shutil
import subprocess
import threading
import unittest

IMAGE = "omd-mcp"
RUN = ["docker", "run", "-i", "--rm", "--read-only", "--pull=never", "--memory=512m", IMAGE]
EXCHANGE_TIMEOUT = 60

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
    call(7, "get_nws_context", {"query": "compath", "limit": 4}),
    call(8, "get_jedi_context", {"query": "ObsGroup", "limit": 4}),
]
EXPECTED_IDS = {1, 2, 3, 4, 5, 6, 7, 8}


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
            stderr=subprocess.PIPE, text=True)
        responses = {}
        stdout_lines = queue.Queue()
        stderr_parts = []

        def _read_stdout():
            try:
                for line in proc.stdout:
                    stdout_lines.put(line)
            finally:
                stdout_lines.put(None)

        def _read_stderr():
            try:
                stderr_parts.append(proc.stderr.read())
            except Exception:
                pass

        threading.Thread(target=_read_stdout, daemon=True).start()
        threading.Thread(target=_read_stderr, daemon=True).start()

        def _stderr_tail():
            return "".join(stderr_parts)[-500:]

        def _fail_missing(deadline_ids):
            tail = _stderr_tail()
            suffix = f"\nstderr tail: {tail}" if tail else ""
            self.fail(
                f"server closed stdout before answering ids {sorted(deadline_ids)}"
                f"{suffix}"
            )

        try:
            for msg in REQUESTS:
                proc.stdin.write(json.dumps(msg) + "\n")
                proc.stdin.flush()
            # Read one response per request id; do NOT close stdin first.
            deadline_ids = set(EXPECTED_IDS)
            while deadline_ids:
                try:
                    line = stdout_lines.get(timeout=EXCHANGE_TIMEOUT)
                except queue.Empty:
                    proc.terminate()
                    tail = _stderr_tail()
                    suffix = f"\nstderr tail: {tail}" if tail else ""
                    self.fail(
                        f"timed out waiting for ids {sorted(deadline_ids)}"
                        f" after {EXCHANGE_TIMEOUT}s{suffix}"
                    )
                if line is None:
                    _fail_missing(deadline_ids)
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
            try:
                proc.stdout.close()
            except Exception:
                pass
            try:
                proc.stderr.close()
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
            "get_nws_context", "get_jedi_context", "list_collections"})

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
        self.assertEqual(units.get(("nws-hpc-standards", "11.0.0")), 22)
        self.assertEqual(units.get(("jedi", "snapshot-7cd222915252")), 1900)

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