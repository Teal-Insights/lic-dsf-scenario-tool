"""Serve the in-browser application on loopback.

    python poc/browser/serve.py

``/`` is the five-step workspace. ``/index.html`` is the smaller calculation
page. Both run the pinned library in Pyodide. Workbook bytes chosen by the
analyst are not received by this server. The official illustrative template
is fetched here only after the analyst asks for it, because the publisher
does not allow that download from the browser. The pinned Python runtime is
read from the public site when the page requests it. HEAD uses the same
generated page, fonts and official example as GET, and omits the body.
"""
from __future__ import annotations

import argparse
import urllib.error
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from build_wheels import DEST, PYODIDE_INDEX, build
from lic_dsf.official_example import download_official_example, verify_official_example

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FONTS = ROOT / "src" / "lic_dsf" / "fonts"
FONT_NAMES = {"Inter-Regular.otf", "Inter-SemiBold.otf", "IBMPlexSerif-SemiBold.otf"}
EXAMPLE_CACHE = Path.home() / ".local" / "share" / "lic-dsf-browser-poc" / "official-example.xlsm"
PYODIDE_ORIGIN = "https://d3iptw2fvdc3fp.cloudfront.net"
_PYODIDE_HOST = "d3iptw2fvdc3fp.cloudfront.net"
_RUNTIME_UNAVAILABLE = "The calculation runtime is unavailable."
BANNER = (
    '<div id="browserRuntime" role="status" style="max-width:1176px;margin:12px auto 0;padding:12px 18px;'
    'background:#f2f8fa;border-left:4px solid #143e5a;font:16px/1.45 Inter,system-ui,sans-serif">'
    "Starting the in-browser calculation runtime. The first start downloads it and can take several minutes. "
    "Your workbook stays in this browser.</div>\n"
)


def application_page() -> bytes:
    page = (ROOT / "src" / "lic_dsf" / "web.html").read_text(encoding="utf-8")
    page = page.replace(
        '<meta charset="utf-8">',
        '<meta charset="utf-8"><script src="/browser-bridge.js"></script>',
        1,
    )
    page = page.replace("<body>\n", "<body>\n" + BANNER, 1)
    page = page.replace(">Local workspace<", ">In-browser application<", 1)
    return page.encode("utf-8")


def official_example_bytes() -> bytes:
    if EXAMPLE_CACHE.is_file():
        try:
            return verify_official_example(EXAMPLE_CACHE.read_bytes())
        except ValueError:
            EXAMPLE_CACHE.unlink()
    payload = download_official_example()
    EXAMPLE_CACHE.parent.mkdir(parents=True, exist_ok=True)
    temporary = EXAMPLE_CACHE.with_suffix(".xlsm.partial")
    temporary.write_bytes(payload)
    temporary.replace(EXAMPLE_CACHE)
    return payload


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _send(self, status, content_type, body):
        payload = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    def _runtime_name(self, path: str) -> str | None:
        if not path.startswith(PYODIDE_INDEX):
            return None
        name = path[len(PYODIDE_INDEX):]
        if not name or "/" in name or "\\" in name or name in {".", ".."}:
            return ""
        return name

    def _proxy_runtime(self, path: str) -> bool:
        name = self._runtime_name(path)
        if name is None:
            return False
        if not name:
            self._send(404, "text/plain; charset=utf-8", "Not found.")
            return True
        request = urllib.request.Request(PYODIDE_ORIGIN + PYODIDE_INDEX + name, method=self.command)
        try:
            response = urllib.request.urlopen(request, timeout=180)
        except urllib.error.HTTPError as exc:
            self._send(404 if exc.code == 404 else 502, "text/plain; charset=utf-8", _RUNTIME_UNAVAILABLE)
            return True
        except urllib.error.URLError:
            self._send(502, "text/plain; charset=utf-8", _RUNTIME_UNAVAILABLE)
            return True
        with response:
            host = (urlsplit(response.geturl()).hostname or "").lower()
            if host != _PYODIDE_HOST:
                self._send(502, "text/plain; charset=utf-8", _RUNTIME_UNAVAILABLE)
                return True
            content_type = response.headers.get("Content-Type", "application/octet-stream")
            if "\r" in content_type or "\n" in content_type:
                content_type = "application/octet-stream"
            if self.command == "HEAD":
                length = response.headers.get("Content-Length")
                payload = b"" if length is not None else response.read()
                declared = length if length is not None else str(len(payload))
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", declared)
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                return True
            payload = response.read()
        self._send(200, content_type, payload)
        return True

    def _dynamic(self):
        path = urlsplit(self.path).path
        if self._proxy_runtime(path):
            return True
        if path in ("/", "/app"):
            self._send(200, "text/html; charset=utf-8", application_page())
            return True
        if path.startswith("/fonts/"):
            name = path.rsplit("/", 1)[-1]
            font = FONTS / name
            if name not in FONT_NAMES or not font.is_file():
                self._send(404, "text/plain; charset=utf-8", "Not found.")
            else:
                self._send(200, "font/otf", font.read_bytes())
            return True
        if path == "/official-example.xlsm":
            try:
                payload = official_example_bytes()
            except ValueError as exc:
                message = str(exc)
                if len(message) > 400 or "/" in message or "\\" in message:
                    message = "The official example could not be downloaded."
                self._send(400, "application/json", '{"error":"' + message.replace('"', "") + '"}')
            else:
                self._send(200, "application/vnd.ms-excel.sheet.macroEnabled.12", payload)
            return True
        return False

    def do_HEAD(self):
        if not self._dynamic():
            super().do_HEAD()

    def do_GET(self):
        if not self._dynamic():
            super().do_GET()


def main():
    parser = argparse.ArgumentParser(description="Serve the in-browser LIC-DSF application.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    if args.rebuild or not any(DEST.glob("*.whl")) or not (HERE / "manifest.json").is_file():
        build()

    handler = partial(Handler, directory=str(HERE))
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"Full application: http://127.0.0.1:{args.port}/", flush=True)
    print(f"Calculation page: http://127.0.0.1:{args.port}/index.html", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
