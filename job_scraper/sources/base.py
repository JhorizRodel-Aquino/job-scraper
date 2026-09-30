"""Shared interface and HTTP helpers for source adapters.

Every module in `job_scraper.sources` must expose:

    NAME: str
    def fetch() -> list[RawJob]: ...

`fetch()` should not raise on a single bad record — skip it and keep going,
since one malformed listing shouldn't take down the whole source.
"""

from __future__ import annotations

import httpx

REQUEST_TIMEOUT = 20.0
USER_AGENT = "job-scraper/0.1 (personal project; contact via repo owner)"


def get_client() -> httpx.Client:
    return httpx.Client(
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    )
