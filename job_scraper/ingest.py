"""Manual single-URL ingestion: paste a job posting URL you found yourself,
scrape its structured data, and store it. Hybrid of manual search +
automated capture — you do the browsing/filtering, this just saves the
structured record instead of you retyping it.

Parses the schema.org `JobPosting` JSON-LD block that job sites embed for
Google Jobs indexing (not site-specific — works for any site that has it,
confirmed for LinkedIn's public guest job pages).

Some sites (confirmed: Jobstreet, Indeed) block a plain HTTP request outright
(Cloudflare-style bot protection), even for a single page. For those, this
falls back to a real headless browser via Playwright — not installed by
default, run `playwright install chromium` once to enable the fallback.
"""

from __future__ import annotations

import json
import re
from typing import Any

from job_scraper.models import RawJob
from job_scraper.sources.base import get_client

BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

_JSONLD_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.S | re.I,
)


def _extract_job_posting(html: str) -> dict[str, Any] | None:
    for block in _JSONLD_RE.findall(html):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        for candidate in data if isinstance(data, list) else [data]:
            if isinstance(candidate, dict) and candidate.get("@type") == "JobPosting":
                return candidate
    return None


def _fetch_plain(url: str) -> str | None:
    with get_client() as client:
        try:
            resp = client.get(url, headers={"User-Agent": BROWSER_USER_AGENT})
        except Exception:
            return None
        return resp.text if resp.status_code == 200 else None


def _fetch_rendered(url: str) -> str | None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(user_agent=BROWSER_USER_AGENT)
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
            html = page.content()
            browser.close()
            return html
    except Exception:
        return None


def _location_str(job_location: Any) -> str | None:
    if isinstance(job_location, list):
        job_location = job_location[0] if job_location else None
    if not isinstance(job_location, dict):
        return None
    address = job_location.get("address")
    if isinstance(address, str):
        return address
    if not isinstance(address, dict):
        return None
    parts = [
        address.get("addressLocality"),
        address.get("addressRegion"),
        address.get("addressCountry"),
    ]
    return ", ".join(p for p in parts if p) or None


def fetch_job_posting(url: str) -> RawJob | None:
    """Fetch and parse a single job posting URL. Returns None if the page
    couldn't be fetched or has no JobPosting structured data."""
    html = _fetch_plain(url)
    data = _extract_job_posting(html) if html else None
    if data is None:
        html = _fetch_rendered(url)
        data = _extract_job_posting(html) if html else None
    if data is None:
        return None

    org = data.get("hiringOrganization")
    company = org.get("name") if isinstance(org, dict) else None

    return RawJob(
        source="ingest",
        title=data.get("title") or "",
        company=company or "Unknown",
        location=_location_str(data.get("jobLocation")),
        remote=data.get("jobLocationType") == "TELECOMMUTE",
        url=url,
        description=data.get("description"),
        raw=data,
    )
