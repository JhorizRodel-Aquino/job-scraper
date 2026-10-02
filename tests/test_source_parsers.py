import httpx
import respx

from job_scraper.sources import greenhouse, jooble, lever


@respx.mock
def test_jooble_fetch_parses_jobs(monkeypatch) -> None:
    monkeypatch.setenv("JOOBLE_API_KEY", "test-key")
    respx.post(url__regex=r"^https://jooble\.org/api/.*").mock(
        return_value=httpx.Response(
            200,
            json={
                "jobs": [
                    {
                        "id": 42,
                        "title": "Backend Developer",
                        "company": "Acme PH",
                        "location": "Manila, Philippines",
                        "link": "https://jooble.org/job/42",
                        "snippet": "desc",
                        "updated": "2024-02-01T00:00:00",
                    }
                ]
            },
        )
    )

    jobs = jooble.fetch()

    assert len(jobs) == 1
    job = jobs[0]
    assert job.source == "jooble"
    assert job.external_id == "42"
    assert job.title == "Backend Developer"
    assert job.company == "Acme PH"


def test_jooble_fetch_returns_empty_without_api_key(monkeypatch) -> None:
    monkeypatch.delenv("JOOBLE_API_KEY", raising=False)
    assert jooble.fetch() == []


@respx.mock
def test_greenhouse_fetch_parses_jobs() -> None:
    respx.get(url__regex=r"^https://boards-api\.greenhouse\.io/.*").mock(
        return_value=httpx.Response(
            200,
            json={
                "jobs": [
                    {
                        "id": 1,
                        "title": "Software Engineer",
                        "location": {"name": "Remote in the Philippines"},
                        "absolute_url": "https://job-boards.greenhouse.io/x/jobs/1",
                        "updated_at": "2024-01-15T00:00:00Z",
                    }
                ]
            },
        )
    )

    jobs = greenhouse.fetch()

    # One mocked response matches every company-board request.
    assert len(jobs) == len(greenhouse.GREENHOUSE_COMPANIES)
    job = jobs[0]
    assert job.source == "greenhouse"
    assert job.title == "Software Engineer"
    assert job.remote is True
    assert job.location == "Remote in the Philippines"


@respx.mock
def test_lever_fetch_parses_jobs() -> None:
    respx.get(url__regex=r"^https://api\.lever\.co/.*").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": "abc",
                    "text": "Senior Full-Stack Developer",
                    "categories": {"location": "Makati City, Metro Manila"},
                    "hostedUrl": "https://jobs.lever.co/x/abc",
                    "createdAt": 1700000000000,
                }
            ],
        )
    )

    jobs = lever.fetch()

    job = jobs[0]
    assert job.source == "lever"
    assert job.title == "Senior Full-Stack Developer"
    assert job.location == "Makati City, Metro Manila"
