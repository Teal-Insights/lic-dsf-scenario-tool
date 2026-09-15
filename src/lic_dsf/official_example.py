"""Explicit, fixed-source retrieval of the publisher's illustrative workbook."""
from __future__ import annotations

import hashlib
import time
import urllib.request
from urllib.parse import urlsplit

OFFICIAL_EXAMPLE_SHA = "3a0a0b80c7cbc95ac953f25ecae0b437129d669ceb8aeefb54ab86dc8727ea86"
OFFICIAL_EXAMPLE_BYTES = 5504930
OFFICIAL_EXAMPLE_URL = "https://thedocs.worldbank.org/en/doc/f0ade6bcf85b6f98dbeb2c39a2b7770c-0360012025/original/LIC-DSF-IDA21-Template-08-12-2025-vf.xlsm"


def verify_official_example(payload):
    """Reject changed publisher downloads rather than silently changing examples."""
    if len(payload) != OFFICIAL_EXAMPLE_BYTES or hashlib.sha256(payload).hexdigest() != OFFICIAL_EXAMPLE_SHA:
        raise ValueError("The example does not match the supported official file. No example was loaded. Use the documented original template or contact the maintainer.")
    return payload


class _PublisherRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urlsplit(newurl)
        if target.scheme != "https" or target.hostname != "thedocs.worldbank.org" or target.username or target.password or target.port not in (None, 443):
            raise ValueError("The publisher redirected the example outside its expected secure download site. No example was loaded.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download_official_example():
    """Fetch only on user request; transmit no workbook, scenario or workspace data."""
    request = urllib.request.Request(OFFICIAL_EXAMPLE_URL, headers={"User-Agent": "LIC-DSF-Scenario-Tool", "Accept": "application/octet-stream", "Accept-Encoding": "identity"})
    opener = urllib.request.build_opener(_PublisherRedirect())
    try:
        with opener.open(request, timeout=20) as response:
            if response.status != 200:
                raise ValueError("The official example could not be downloaded. Check your connection and try again, or upload the documented original template.")
            length = response.headers.get("Content-Length")
            if length is not None and int(length) != OFFICIAL_EXAMPLE_BYTES:
                raise ValueError("The publisher returned a different file size. No example was loaded.")
            deadline = time.monotonic() + 60
            chunks = []
            remaining = OFFICIAL_EXAMPLE_BYTES + 1
            while remaining:
                if time.monotonic() > deadline:
                    raise ValueError("The example download took too long. Check your connection and try again.")
                chunk = response.read(min(65536, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
        return verify_official_example(b"".join(chunks))
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("The official example could not be downloaded. Check your internet connection and try again. You can also upload the documented original template; saved work is retained.") from exc
