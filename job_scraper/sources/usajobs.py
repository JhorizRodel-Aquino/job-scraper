"""USAJobs — official US federal job listings API. Requires a free API key.

Set USAJOBS_API_KEY and USAJOBS_USER_AGENT (your registered email) in .env.
If unset, fetch() returns an empty list rather than failing the whole run.
"""

from __future__ import annotations

import os
from datetime import date, datetime

from dotenv import load_dotenv

from job_scraper.models import RawJob
from job_scraper.sources.base import get_client

NAME = "usajobs"
API_URL = "https://data.usajobs.gov/api/search"

load_dotenv()


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def fetch() -> list[RawJob]:
    api_key = os.environ.get("USAJOBS_API_KEY")
    user_agent = os.environ.get("USAJOBS_USER_AGENT")
    if not api_key or not user_agent:
        return []

    headers = {
        "Host": "data.usajobs.gov",
        "User-Agent": user_agent,
        "Authorization-Key": api_key,
    }
    params = {"Keyword": "software engineer", "ResultsPerPage": "500"}

    with get_client() as client:
        resp = client.get(API_URL, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

    jobs: list[RawJob] = []
    for item in data.get("SearchResult", {}).get("SearchResultItems", []):
        descriptor = item.get("MatchedObjectDescriptor", {})
        try:
            remuneration = (descriptor.get("PositionRemuneration") or [{}])[0]
            jobs.append(
                RawJob(
                    source=NAME,
                    external_id=descriptor.get("PositionID"),
                    title=descriptor.get("PositionTitle", ""),
                    company=descriptor.get("OrganizationName", "US Government"),
                    location=descriptor.get("PositionLocationDisplay"),
                    remote="remote" in (descriptor.get("PositionLocationDisplay") or "").lower(),
                    url=descriptor.get("PositionURI", ""),
                    description=descriptor.get("UserArea", {})
                    .get("Details", {})
                    .get("JobSummary"),
                    posted_date=_parse_date(descriptor.get("PublicationStartDate")),
                    salary_min=float(remuneration.get("MinimumRange"))
                    if remuneration.get("MinimumRange")
                    else None,
                    salary_max=float(remuneration.get("MaximumRange"))
                    if remuneration.get("MaximumRange")
                    else None,
                    raw=descriptor,
                )
            )
        except Exception:
            continue
    return jobs
