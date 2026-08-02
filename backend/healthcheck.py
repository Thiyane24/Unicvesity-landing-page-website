#!/usr/bin/env python
"""
Standalone healthcheck used by compose to verify the API is up.

Why a separate script?
- Lets compose hit a process-level check without needing curl in the
  API container's image.
- Keeps container deps small.

Usage (from inside the api container, or anywhere with network access):
    python healthcheck.py http://127.0.0.1:8000/api/health
"""
from __future__ import annotations

import sys
from urllib import request
from urllib.error import URLError


def main(url: str) -> int:
    try:
        with request.urlopen(url, timeout=3) as r:
            ok = 200 <= r.status < 300
            sys.exit(0 if ok else 1)
    except (URLError, TimeoutError, OSError):
        sys.exit(1)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/api/health"
    sys.exit(main(target))
