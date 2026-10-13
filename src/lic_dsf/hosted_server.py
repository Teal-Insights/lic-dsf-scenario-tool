"""Single-process production WSGI server, normally behind a TLS reverse proxy."""
import logging
import os
from waitress import serve
from .hosted import create_app

def main():
    # Payloads, cookies, query strings and exception traces are never application logs.
    logging.disable(logging.CRITICAL)
    app = create_app()
    try:
        serve(app, listen='0.0.0.0:8080', threads=2, connection_limit=24, backlog=16,
            channel_timeout=15, cleanup_interval=5, max_request_body_size=131072,
            max_request_header_size=8192, inbuf_overflow=131073,
            outbuf_overflow=33554433, outbuf_high_watermark=33554433,
            expose_tracebacks=False, log_socket_errors=False, clear_untrusted_proxy_headers=True)
    finally:
        app.close()

if __name__ == '__main__':
    main()
