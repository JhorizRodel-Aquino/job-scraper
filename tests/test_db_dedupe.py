import sqlite3

import pytest

from job_scraper.db import compute_job_id, get_connection, init_db, query_jobs, upsert_job
from job_scraper.models import Job, RawJob


@pytest.fixture
def conn():
    connection = get_connection(":memory:")
    init_db(connection)
    yield connection
    connection.close()


def _make_job(**overrides) -> Job:
    fields = dict(
        source="test",
        external_id="123",
        title="Backend Engineer",
        company="Acme",
        location="Remote",
        remote=True,
        url="https://example.com/jobs/123",
    )
    fields.update(overrides)
    raw = RawJob(**fields)
    return Job(**raw.model_dump(), id=compute_job_id(raw), sub_role="backend")


def test_upsert_inserts_new_job(conn: sqlite3.Connection) -> None:
    job = _make_job()
    upsert_job(conn, job)
    conn.commit()

    rows = query_jobs(conn)
    assert len(rows) == 1
    assert rows[0]["title"] == "Backend Engineer"


def test_upsert_same_job_twice_does_not_duplicate(conn: sqlite3.Connection) -> None:
    job = _make_job()
    upsert_job(conn, job)
    conn.commit()
    upsert_job(conn, job)
    conn.commit()

    rows = query_jobs(conn)
    assert len(rows) == 1


def test_upsert_updates_last_seen_at(conn: sqlite3.Connection) -> None:
    job = _make_job()
    upsert_job(conn, job)
    conn.commit()
    first_seen = query_jobs(conn)[0]["first_seen_at"]

    upsert_job(conn, job)
    conn.commit()
    row = query_jobs(conn)[0]

    assert row["first_seen_at"] == first_seen
    assert row["last_seen_at"] >= first_seen


def test_compute_job_id_falls_back_without_external_id() -> None:
    raw1 = RawJob(
        source="wwr", title="Backend Engineer", company="Acme", url="https://x.com/1"
    )
    raw2 = RawJob(
        source="wwr", title="Backend Engineer", company="Acme", url="https://x.com/2"
    )
    # Same source/company/title/location -> same fingerprint even with a
    # different URL, since WWR-style sources don't give a stable external id.
    assert compute_job_id(raw1) == compute_job_id(raw2)


def test_query_filters_by_role(conn: sqlite3.Connection) -> None:
    backend = _make_job(external_id="1")
    frontend_raw = RawJob(
        source="test",
        external_id="2",
        title="Frontend Engineer",
        company="Acme",
        url="https://example.com/jobs/2",
    )
    frontend = Job(
        **frontend_raw.model_dump(), id=compute_job_id(frontend_raw), sub_role="frontend"
    )

    upsert_job(conn, backend)
    upsert_job(conn, frontend)
    conn.commit()

    rows = query_jobs(conn, role="frontend")
    assert len(rows) == 1
    assert rows[0]["sub_role"] == "frontend"
