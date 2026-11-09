"""Serve the in-browser proof of concept on loopback.

    python poc/browser/serve.py

``/`` is the five-step workspace. ``/index.html`` is the smaller calculation
page. Both run the pinned library in Pyodide. Workbook bytes chosen by the
analyst are not received by this server. The official illustrative template
is fetched here only after the analyst asks for it, because the publisher
does not allow that download from the browser.
"""
from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from build_wheels import DEST, build
from lic_dsf.official_example import download_official_example, verify_official_example

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FONTS = ROOT / "src" / "lic_dsf" / "fonts"
FONT_NAMES = {"Inter-Regular.otf", "Inter-SemiBold.otf", "IBMPlexSerif-SemiBold.otf"}
EXAMPLE_CACHE = Path.home() / ".local" / "share" / "lic-dsf-browser-poc" / "official-example.xlsm"
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
    page = page.replace(">Local workspace<", ">In-browser proof of concept<", 1)
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


def main():
    parser = argparse.ArgumentParser(description="Serve the in-browser LIC-DSF proof of concept.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    if args.rebuild or not any(DEST.glob("*.whl")) or not (HERE / "manifest.json").is_file():
        build()

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
            self.wfile.write(payload)

        def do_GET(self):
            path = urlsplit(self.path).path
            if path in ("/", "/app"):
                return self._send(200, "text/html; charset=utf-8", application_page())
            if path.startswith("/fonts/"):
                name = path.rsplit("/", 1)[-1]
                font = FONTS / name
                if name not in FONT_NAMES or not font.is_file():
                    return self._send(404, "text/plain; charset=utf-8", "Not found.")
                return self._send(200, "font/otf", font.read_bytes())
            if path == "/official-example.xlsm":
                try:
                    payload = official_example_bytes()
                except ValueError as exc:
                    message = str(exc)
                    if len(message) > 400 or "/" in message or "\\" in message:
                        message = "The official example could not be downloaded."
                    return self._send(400, "application/json", '{"error":"' + message.replace('"', "") + '"}')
                return self._send(200, "application/vnd.ms-excel.sheet.macroEnabled.12", payload)
            return super().do_GET()

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
