"""Arbeitnow — job board API, global listings, no auth."""

from __future__ import annotations

import time
from datetime import date, datetime, timezone

from job_scraper.models import RawJob
from job_scraper.sources.base import get_client

NAME = "arbeitnow"
API_URL = "https://www.arbeitnow.com/api/job-board-api"
MAX_PAGES = 50
PAGE_DELAY_SECONDS = 0.5


def _parse_date(value: object) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc).date()
    except (ValueError, TypeError, OSError):
        return None


def fetch() -> list[RawJob]:
    jobs: list[RawJob] = []
    with get_client() as client:
        url: str | None = API_URL
        # The API paginates; follow `links.next` until exhausted. Bounded by
        # MAX_PAGES as a guard against a misbehaving/self-referential `next`.
        for page_num in range(MAX_PAGES):
            if not url:
                break
            if page_num > 0:
                time.sleep(PAGE_DELAY_SECONDS)
            try:
                resp = client.get(url)
                resp.raise_for_status()
                payload = resp.json()
            except Exception:
                # e.g. a rate limit mid-pagination — keep whatever pages we
                # already parsed instead of discarding the whole fetch.
                break
            for item in payload.get("data", []):
                try:
                    jobs.append(
                        RawJob(
                            source=NAME,
                            external_id=item.get("slug"),
                            title=item.get("title", ""),
                            company=item.get("company_name", "Unknown"),
                            location=item.get("location") or None,
                            remote=bool(item.get("remote", False)),
                            url=item.get("url", ""),
                            description=item.get("description"),
                            posted_date=_parse_date(item.get("created_at")),
                            raw=item,
                        )
                    )
                except Exception:
                    continue
            url = payload.get("links", {}).get("next") or None
    return jobs
