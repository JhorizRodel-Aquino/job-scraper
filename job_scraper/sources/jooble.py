"""Jooble — job aggregator API, scoped to the Philippines. Requires a free API key.

Set JOOBLE_API_KEY in .env. If unset, fetch() returns an empty list rather
than failing the whole run. Register at https://jooble.org/api/about.
"""

from __future__ import annotations

import os
from datetime import date, datetime

from dotenv import load_dotenv

from job_scraper.models import RawJob
from job_scraper.sources.base import get_client

NAME = "jooble"
API_URL = "https://jooble.org/api/{key}"

load_dotenv()


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def fetch() -> list[RawJob]:
    api_key = os.environ.get("JOOBLE_API_KEY")
    if not api_key:
        return []

    with get_client() as client:
        resp = client.post(
            API_URL.format(key=api_key),
            json={"keywords": "software engineer", "location": "Philippines"},
        )
        resp.raise_for_status()
        data = resp.json()

    jobs: list[RawJob] = []
    for item in data.get("jobs", []):
        try:
            location = item.get("location")
            jobs.append(
                RawJob(
                    source=NAME,
                    external_id=str(item.get("id")) if item.get("id") else None,
                    title=item.get("title", ""),
                    company=item.get("company") or "Unknown",
                    location=location,
                    remote="remote" in (location or "").lower(),
                    url=item.get("link", ""),
                    description=item.get("snippet"),
                    posted_date=_parse_date(item.get("updated")),
                    raw=item,
                )
            )
        except Exception:
            continue
    return jobs
