"""Greenhouse — per-company job board API, no auth.

Not a global search: each company publishes its own board. The list of
tracked companies lives in config.GREENHOUSE_COMPANIES, limited to companies
confirmed to post Philippines-located jobs.
"""

from __future__ import annotations

from datetime import date, datetime

from job_scraper.config import GREENHOUSE_COMPANIES
from job_scraper.models import RawJob
from job_scraper.sources.base import get_client

NAME = "greenhouse"
BOARD_URL = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs"


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _fetch_company(client, token: str) -> list[RawJob]:
    resp = client.get(BOARD_URL.format(token=token))
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    data = resp.json()

    jobs: list[RawJob] = []
    for item in data.get("jobs", []):
        try:
            location = (item.get("location") or {}).get("name")
            jobs.append(
                RawJob(
                    source=NAME,
                    external_id=str(item["id"]),
                    title=item.get("title", ""),
                    company=token,
                    location=location,
                    remote="remote" in (location or "").lower(),
                    url=item.get("absolute_url", ""),
                    posted_date=_parse_date(item.get("updated_at")),
                    raw=item,
                )
            )
        except Exception:
            continue
    return jobs


def fetch() -> list[RawJob]:
    jobs: list[RawJob] = []
    with get_client() as client:
        for token in GREENHOUSE_COMPANIES:
            try:
                jobs.extend(_fetch_company(client, token))
            except Exception:
                continue
    return jobs
