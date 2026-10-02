"""Lever — per-company job board API, no auth.

Not a global search: each company publishes its own board. The list of
tracked companies lives in config.LEVER_COMPANIES, limited to companies
confirmed to post Philippines-located jobs.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from job_scraper.config import LEVER_COMPANIES
from job_scraper.models import RawJob
from job_scraper.sources.base import get_client

NAME = "lever"
BOARD_URL = "https://api.lever.co/v0/postings/{token}?mode=json"


def _parse_date(value: object) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc).date()
    except (ValueError, TypeError, OSError):
        return None


def _fetch_company(client, token: str) -> list[RawJob]:
    resp = client.get(BOARD_URL.format(token=token))
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    data = resp.json()

    jobs: list[RawJob] = []
    for item in data:
        try:
            categories = item.get("categories", {})
            location = categories.get("location")
            jobs.append(
                RawJob(
                    source=NAME,
                    external_id=item.get("id"),
                    title=item.get("text", ""),
                    company=token,
                    location=location,
                    remote="remote" in (location or "").lower(),
                    url=item.get("hostedUrl", ""),
                    description=item.get("descriptionPlain"),
                    posted_date=_parse_date(item.get("createdAt")),
                    raw=item,
                )
            )
        except Exception:
            continue
    return jobs


def fetch() -> list[RawJob]:
    jobs: list[RawJob] = []
    with get_client() as client:
        for token in LEVER_COMPANIES:
            try:
                jobs.extend(_fetch_company(client, token))
            except Exception:
                continue
    return jobs
