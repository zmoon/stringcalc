"""Local stdlib HTTP server for ``stringcalc app``."""

from __future__ import annotations

import functools
import http.server
import json
import threading
import urllib.parse
import webbrowser
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ._app import METHODS, dispatch

_WEB_DIR = Path(__file__).resolve().parent / "_web"
_MAX_BODY_BYTES = 1024 * 1024
_DISPATCH_LOCK = threading.Lock()


class _AppHandler(http.server.SimpleHTTPRequestHandler):
    def _send_json(self, status: int, data: Any) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urllib.parse.urlsplit(self.path).path
        if path == "/app-config.json":
            self._send_json(200, {"backend": "http"})
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = urllib.parse.urlsplit(self.path).path
        if not path.startswith("/api/"):
            self._send_json(404, {"error": f"Unknown endpoint: {path}"})
            return

        method = path.removeprefix("/api/")
        if method not in METHODS:
            self._send_json(404, {"error": f"Unknown method: {method}"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "Invalid Content-Length header"})
            return
        if length < 0 or length > _MAX_BODY_BYTES:
            self._send_json(413, {"error": "Request body too large"})
            return

        raw = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            self._send_json(400, {"error": f"Invalid JSON: {e}"})
            return
        if not isinstance(payload, dict):
            self._send_json(400, {"error": "Request body must be a JSON object"})
            return

        with _DISPATCH_LOCK:
            result = dispatch(method, payload)
        self._send_json(200, result)

    def log_message(self, format: str, *args: Any) -> None:
        return


def create_server(
    host: str = "127.0.0.1",
    port: int = 0,
    *,
    web_dir: Path | None = None,
) -> http.server.ThreadingHTTPServer:
    """Create a bound ``ThreadingHTTPServer`` serving the web app and JSON API."""
    root = web_dir or _WEB_DIR
    if not (root / "index.html").is_file():
        raise FileNotFoundError(
            f"Web app assets not found at {root}. "
            "Build them with: npm --prefix frontend run build:app"
        )
    handler = functools.partial(_AppHandler, directory=str(root))
    return http.server.ThreadingHTTPServer((host, port), handler)


def serve(
    *,
    host: str = "127.0.0.1",
    port: int = 0,
    open_browser: bool = True,
    on_ready: Callable[[str], None] | None = None,
) -> None:
    """Serve the interactive web app locally until interrupted."""
    server = create_server(host=host, port=port)
    bound_host, bound_port = server.server_address[0], server.server_address[1]
    display_host = "127.0.0.1" if bound_host in {"", "0.0.0.0"} else str(bound_host)
    url = f"http://{display_host}:{bound_port}/"
    if on_ready is not None:
        on_ready(url)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
