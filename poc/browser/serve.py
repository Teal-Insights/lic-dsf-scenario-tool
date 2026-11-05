"""Serve the browser proof of concept on loopback.

    python poc/browser/serve.py

Build the local wheels first when they are missing. The page then loads
Pyodide from the pinned jsDelivr URL. Workbook bytes are chosen in the
browser and are not received by this server.
"""
from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from build_wheels import DEST, build

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description="Serve the browser calculation proof of concept.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    if args.rebuild or not any(DEST.glob("*.whl")) or not (HERE / "manifest.json").is_file():
        build()
    class Handler(SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

    handler = partial(Handler, directory=str(HERE))
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"Open http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
