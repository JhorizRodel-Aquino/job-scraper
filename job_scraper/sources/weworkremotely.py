"""WeWorkRemotely — per-category RSS feeds, no auth."""

from __future__ import annotations

from datetime import date, datetime

import feedparser

from job_scraper.models import RawJob

NAME = "weworkremotely"

FEED_URLS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
]


def _parse_date(entry) -> date | None:
    parsed = getattr(entry, "published_parsed", None)
    if not parsed:
        return None
    try:
        return datetime(*parsed[:6]).date()
    except (TypeError, ValueError):
        return None


def _split_title(raw_title: str) -> tuple[str, str]:
    """WWR titles are usually 'Company: Job Title'."""
    if ":" in raw_title:
        company, _, title = raw_title.partition(":")
        return company.strip(), title.strip()
    return "Unknown", raw_title.strip()


def fetch() -> list[RawJob]:
    jobs: list[RawJob] = []
    for feed_url in FEED_URLS:
        parsed = feedparser.parse(feed_url)
        for entry in parsed.entries:
            try:
                company, title = _split_title(entry.get("title", ""))
                jobs.append(
                    RawJob(
                        source=NAME,
                        external_id=entry.get("id") or entry.get("link"),
                        title=title,
                        company=company,
                        location=None,
                        remote=True,
                        url=entry.get("link", ""),
                        description=entry.get("summary"),
                        posted_date=_parse_date(entry),
                        raw=dict(entry),
                    )
                )
            except Exception:
                continue
    return jobs
