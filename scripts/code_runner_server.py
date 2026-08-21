#!/usr/bin/env python3
"""Local backend for the lesson code runners (`{% include runners/code.html %}`).

In production the runner posts to flask.opencodingsociety.com and
spring.opencodingsociety.com. On localhost `assets/js/api/config.js` swings those
URLs to http://localhost:8587 and http://localhost:8585, which is why the ▶
button fails locally unless something is listening there. This script is that
something.

    POST http://localhost:8587/run/python      {"code": "..."} -> {"output": "..."}
    POST http://localhost:8587/run/javascript  {"code": "..."} -> {"output": "..."}
    POST http://localhost:8585/run/java        {"code": "..."} -> {"output": "..."}

It executes submitted code with no sandbox, exactly as the real backends do, so
it binds to 127.0.0.1 only and is meant for local authoring. Do not expose it.

    make runners        start (background)
    make stop-runners   stop
"""

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PYTHON_PORT = int(os.environ.get("RUNNER_PYTHON_PORT", "8587"))
JAVA_PORT = int(os.environ.get("RUNNER_JAVA_PORT", "8585"))
TIMEOUT = int(os.environ.get("RUNNER_TIMEOUT", "15"))
MAX_CODE_BYTES = 256 * 1024
DEFAULT_ORIGIN = "http://localhost:4500"

# Matches `public class Foo` / `public final class Foo` etc, to name the .java file.
JAVA_PUBLIC_CLASS = re.compile(
    r"^\s*public\s+(?:final\s+|abstract\s+)?(?:class|interface|enum|record)\s+([A-Za-z_$][\w$]*)",
    re.MULTILINE,
)


def _run(argv, cwd):
    """Run a command, returning combined stdout+stderr. Never raises."""
    try:
        proc = subprocess.run(
            argv,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=TIMEOUT,
            start_new_session=True,
        )
    except subprocess.TimeoutExpired as exc:
        partial = (exc.output or b"").decode("utf-8", "replace")
        return 124, partial + f"\n[timed out after {TIMEOUT}s — infinite loop?]"
    except FileNotFoundError:
        return 127, f"[no such file or directory: '{argv[0]}']"
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def run_python(code):
    with tempfile.TemporaryDirectory(prefix="runner-py-") as tmp:
        path = os.path.join(tmp, "main.py")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(code)
        _, out = _run([sys.executable, "-I", "-u", "main.py"], tmp)
        return out.replace(tmp + os.sep, "")


def run_javascript(code):
    node = shutil.which("node")
    if not node:
        # This exact phrasing trips CodeExecutor's browser-side eval() fallback.
        return "Error: [Errno 2] No such file or directory: 'node'"
    with tempfile.TemporaryDirectory(prefix="runner-js-") as tmp:
        path = os.path.join(tmp, "main.js")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(code)
        _, out = _run([node, "main.js"], tmp)
        return out.replace(tmp + os.sep, "")


def run_java(code):
    javac, java = shutil.which("javac"), shutil.which("java")
    if not javac or not java:
        return ("Error: no JDK on PATH — `javac` and `java` are both required.\n"
                "Install one with: sudo apt install default-jdk")

    match = JAVA_PUBLIC_CLASS.search(code)
    name = match.group(1) if match else "Main"

    with tempfile.TemporaryDirectory(prefix="runner-java-") as tmp:
        with open(os.path.join(tmp, name + ".java"), "w", encoding="utf-8") as handle:
            handle.write(code)
        rc, out = _run([javac, "-nowarn", name + ".java"], tmp)
        if rc != 0:
            return out.replace(tmp + os.sep, "") or "Compilation failed."
        _, out = _run([java, "-cp", ".", name], tmp)
        return out.replace(tmp + os.sep, "")


ROUTES = {
    "/run/python": run_python,
    "/run/javascript": run_javascript,
    "/run/java": run_java,
}


class RunnerHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "LocalCodeRunner/1.0"

    def _cors(self):
        # credentials:'include' on the client forbids a wildcard origin, so echo it back.
        origin = self.headers.get("Origin") or DEFAULT_ORIGIN
        requested = self.headers.get("Access-Control-Request-Headers")
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", requested or "Content-Type, X-Origin")
        self.send_header("Access-Control-Max-Age", "86400")
        self.send_header("Vary", "Origin")

    def _json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        if self.path in ("/", "/health"):
            self._json(200, {"status": "ok", "routes": sorted(ROUTES)})
        else:
            self._json(404, {"output": f"Error: unknown route {self.path}"})

    def do_POST(self):
        handler = ROUTES.get(self.path.split("?")[0])
        if handler is None:
            self._json(404, {"output": f"Error: unknown route {self.path}"})
            return

        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_CODE_BYTES:
            self._json(413, {"output": "Error: code too large"})
            return

        raw = self.rfile.read(length) if length else b"{}"
        try:
            code = json.loads(raw.decode("utf-8")).get("code", "")
        except (ValueError, UnicodeDecodeError) as exc:
            self._json(400, {"output": f"Error: bad request body ({exc})"})
            return

        try:
            output = handler(code)
        except Exception as exc:  # a crash here must not take the server down
            output = f"Error: runner failed ({exc.__class__.__name__}: {exc})"
        self._json(200, {"output": output})

    def log_message(self, fmt, *args):
        sys.stderr.write("[runner] %s - %s\n" % (self.address_string(), fmt % args))


def serve(port):
    httpd = ThreadingHTTPServer(("127.0.0.1", port), RunnerHandler)
    httpd.daemon_threads = True
    return httpd


def main():
    servers = [serve(PYTHON_PORT), serve(JAVA_PORT)]
    for httpd in servers:
        threading.Thread(target=httpd.serve_forever, daemon=True).start()

    print(f"[runner] python/javascript -> http://localhost:{PYTHON_PORT}/run/{{python,javascript}}")
    print(f"[runner] java               -> http://localhost:{JAVA_PORT}/run/java")
    print(f"[runner] python={sys.executable} node={shutil.which('node') or 'MISSING'} "
          f"javac={shutil.which('javac') or 'MISSING'}", flush=True)

    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    stop.wait()

    print("[runner] shutting down", flush=True)
    for httpd in servers:
        httpd.shutdown()


if __name__ == "__main__":
    main()
