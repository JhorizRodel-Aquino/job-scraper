import httpx
import respx

from job_scraper.sources import arbeitnow, remoteok


@respx.mock
def test_remoteok_fetch_parses_jobs_and_skips_legal_notice() -> None:
    respx.get(remoteok.API_URL).mock(
        return_value=httpx.Response(
            200,
            json=[
                {"legal": "some notice, not a job"},
                {
                    "id": "111",
                    "position": "Backend Engineer",
                    "company": "Acme",
                    "location": "Worldwide",
                    "url": "https://remoteok.com/l/111",
                    "date": "2024-01-15T00:00:00+00:00",
                },
            ],
        )
    )

    jobs = remoteok.fetch()

    assert len(jobs) == 1
    job = jobs[0]
    assert job.source == "remoteok"
    assert job.external_id == "111"
    assert job.title == "Backend Engineer"
    assert job.company == "Acme"
    assert job.remote is True
    assert job.posted_date is not None


@respx.mock
def test_arbeitnow_fetch_follows_pagination() -> None:
    page1 = {
        "data": [
            {
                "slug": "job-1",
                "title": "Frontend Engineer",
                "company_name": "Beta",
                "location": "Berlin",
                "remote": False,
                "url": "https://arbeitnow.com/job-1",
                "created_at": 1700000000,
            }
        ],
        "links": {"next": "https://www.arbeitnow.com/api/job-board-api?page=2"},
    }
    page2 = {
        "data": [
            {
                "slug": "job-2",
                "title": "DevOps Engineer",
                "company_name": "Gamma",
                "location": "Remote",
                "remote": True,
                "url": "https://arbeitnow.com/job-2",
                "created_at": 1700000001,
            }
        ],
        "links": {"next": None},
    }

    # A single route with sequential side effects, since respx matches on
    # path and ignores query strings unless `params=` is given explicitly —
    # two separately-registered routes for `...` and `...?page=2` would both
    # match the same requests and the first one registered would win for
    # every call, looping forever on page1's `next` link.
    respx.get(url__regex=r"^https://www\.arbeitnow\.com/api/job-board-api").mock(
        side_effect=[
            httpx.Response(200, json=page1),
            httpx.Response(200, json=page2),
        ]
    )

    jobs = arbeitnow.fetch()

    assert len(jobs) == 2
    assert {job.external_id for job in jobs} == {"job-1", "job-2"}
    remote_job = next(job for job in jobs if job.external_id == "job-2")
    assert remote_job.remote is True
