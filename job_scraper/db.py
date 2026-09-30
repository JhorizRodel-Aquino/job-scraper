"""SQLite schema, connection handling, and upsert/dedupe/query logic."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from job_scraper.config import STALE_AFTER_DAYS
from job_scraper.models import Job, RawJob

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "jobs.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    external_id TEXT,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    remote INTEGER NOT NULL DEFAULT 0,
    sub_role TEXT,
    url TEXT NOT NULL,
    description TEXT,
    posted_date TEXT,
    salary_min REAL,
    salary_max REAL,
    raw_json TEXT,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_jobs_sub_role ON jobs(sub_role);
CREATE INDEX IF NOT EXISTS idx_jobs_last_seen_at ON jobs(last_seen_at);
"""


def get_connection(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def compute_job_id(raw: RawJob) -> str:
    """Stable identity for dedup: (source, external_id) when available,
    else a normalized (company, title, location) fingerprint."""
    if raw.external_id:
        key = f"{raw.source}:{raw.external_id}"
    else:
        key = "|".join(
            part.strip().lower()
            for part in (raw.source, raw.company, raw.title, raw.location or "")
        )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]


def upsert_job(conn: sqlite3.Connection, job: Job) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO jobs (
            id, source, external_id, title, company, location, remote,
            sub_role, url, description, posted_date, salary_min, salary_max,
            raw_json, first_seen_at, last_seen_at
        ) VALUES (
            :id, :source, :external_id, :title, :company, :location, :remote,
            :sub_role, :url, :description, :posted_date, :salary_min, :salary_max,
            :raw_json, :first_seen_at, :last_seen_at
        )
        ON CONFLICT(id) DO UPDATE SET
            title=excluded.title,
            company=excluded.company,
            location=excluded.location,
            remote=excluded.remote,
            sub_role=excluded.sub_role,
            url=excluded.url,
            description=excluded.description,
            posted_date=excluded.posted_date,
            salary_min=excluded.salary_min,
            salary_max=excluded.salary_max,
            raw_json=excluded.raw_json,
            last_seen_at=excluded.last_seen_at
        """,
        {
            "id": job.id,
            "source": job.source,
            "external_id": job.external_id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "remote": int(job.remote),
            "sub_role": job.sub_role,
            "url": job.url,
            "description": job.description,
            "posted_date": job.posted_date.isoformat() if job.posted_date else None,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "raw_json": json.dumps(job.raw),
            "first_seen_at": now,
            "last_seen_at": now,
        },
    )


def query_jobs(
    conn: sqlite3.Connection,
    role: str | None = None,
    remote: bool | None = None,
    since_days: int | None = None,
    include_stale: bool = False,
) -> list[sqlite3.Row]:
    clauses = []
    params: dict[str, object] = {}

    if role:
        clauses.append("sub_role = :role")
        params["role"] = role
    if remote is not None:
        clauses.append("remote = :remote")
        params["remote"] = int(remote)
    if since_days is not None:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=since_days)).isoformat()
        clauses.append("last_seen_at >= :since_cutoff")
        params["since_cutoff"] = cutoff
    if not include_stale:
        stale_cutoff = (
            datetime.now(timezone.utc) - timedelta(days=STALE_AFTER_DAYS)
        ).isoformat()
        clauses.append("last_seen_at >= :stale_cutoff")
        params["stale_cutoff"] = stale_cutoff

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(
        f"SELECT * FROM jobs {where} ORDER BY last_seen_at DESC", params
    ).fetchall()
    return rows
