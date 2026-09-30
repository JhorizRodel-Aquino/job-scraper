"""Ashby — per-company job board API, no auth.

Not a global search: each company publishes its own board. The list of
tracked companies lives in config.ASHBY_COMPANIES.
"""

from __future__ import annotations

from datetime import date, datetime

from job_scraper.config import ASHBY_COMPANIES
from job_scraper.models import RawJob
from job_scraper.sources.base import get_client

NAME = "ashby"
BOARD_URL = "https://api.ashbyhq.com/posting-api/job-board/{name}"


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _fetch_company(client, name: str) -> list[RawJob]:
    resp = client.get(BOARD_URL.format(name=name))
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    data = resp.json()

    jobs: list[RawJob] = []
    for item in data.get("jobs", []):
        try:
            jobs.append(
                RawJob(
                    source=NAME,
                    external_id=item.get("id"),
                    title=item.get("title", ""),
                    company=name,
                    location=item.get("location"),
                    remote=bool(item.get("isRemote", False)),
                    url=item.get("jobUrl", ""),
                    description=item.get("descriptionPlain"),
                    posted_date=_parse_date(item.get("publishedAt")),
                    raw=item,
                )
            )
        except Exception:
            continue
    return jobs


def fetch() -> list[RawJob]:
    jobs: list[RawJob] = []
    with get_client() as client:
        for name in ASHBY_COMPANIES:
            try:
                jobs.extend(_fetch_company(client, name))
            except Exception:
                continue
    return jobs
