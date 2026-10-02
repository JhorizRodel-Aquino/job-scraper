"""Orchestrates fetch -> classify -> dedupe/store across all sources."""

from __future__ import annotations

import sqlite3

from job_scraper.classify import classify_sub_role, is_philippines, is_relevant
from job_scraper.db import compute_job_id, upsert_job
from job_scraper.models import Job, RawJob
from job_scraper.sources import ALL_SOURCES


def normalize_and_classify(raw: RawJob) -> Job | None:
    if not raw.title or not is_relevant(raw.title):
        return None
    if not is_philippines(raw.location):
        return None
    return Job(
        **raw.model_dump(),
        id=compute_job_id(raw),
        sub_role=classify_sub_role(raw.title),
    )


def run(conn: sqlite3.Connection) -> dict[str, int]:
    """Fetch every source, classify, and upsert into the DB.

    Returns a per-source count of jobs stored (post-relevance-filter), for
    the caller to report. A source that raises is skipped, not fatal.
    """
    stored_counts: dict[str, int] = {}
    for source in ALL_SOURCES:
        name = source.NAME
        try:
            raw_jobs = source.fetch()
        except Exception as exc:
            print(f"[{name}] fetch failed: {exc}")
            stored_counts[name] = 0
            continue

        count = 0
        for raw in raw_jobs:
            job = normalize_and_classify(raw)
            if job is None:
                continue
            upsert_job(conn, job)
            count += 1
        conn.commit()
        stored_counts[name] = count

    return stored_counts
