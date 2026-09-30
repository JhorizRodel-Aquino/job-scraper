"""RemoteOK — global remote job board, public JSON API, no auth."""

from __future__ import annotations

from datetime import date, datetime

from job_scraper.models import RawJob
from job_scraper.sources.base import get_client

NAME = "remoteok"
API_URL = "https://remoteok.com/api"


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def fetch() -> list[RawJob]:
    with get_client() as client:
        resp = client.get(API_URL)
        resp.raise_for_status()
        data = resp.json()

    jobs: list[RawJob] = []
    for item in data:
        # The first element is a legal/metadata notice, not a job.
        if not isinstance(item, dict) or "id" not in item or "position" not in item:
            continue
        try:
            jobs.append(
                RawJob(
                    source=NAME,
                    external_id=str(item["id"]),
                    title=item.get("position", ""),
                    company=item.get("company", "Unknown"),
                    location=item.get("location") or None,
                    remote=True,
                    url=item.get("url") or f"https://remoteok.com/l/{item['id']}",
                    description=item.get("description"),
                    posted_date=_parse_date(item.get("date")),
                    raw=item,
                )
            )
        except Exception:
            continue
    return jobs
