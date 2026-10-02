import httpx
import respx

from job_scraper.ingest import fetch_job_posting

JOBPOSTING_HTML = """
<html><head>
<script type="application/ld+json">
{
  "@type": "JobPosting",
  "title": "Backend Engineer",
  "hiringOrganization": {"@type": "Organization", "name": "Acme PH"},
  "jobLocation": {
    "@type": "Place",
    "address": {
      "@type": "PostalAddress",
      "addressLocality": "Taguig",
      "addressCountry": "PH"
    }
  },
  "description": "Build things."
}
</script>
</head><body></body></html>
"""


@respx.mock
def test_fetch_job_posting_parses_jsonld() -> None:
    respx.get("https://example.com/job/1").mock(
        return_value=httpx.Response(200, text=JOBPOSTING_HTML)
    )

    job = fetch_job_posting("https://example.com/job/1")

    assert job is not None
    assert job.source == "ingest"
    assert job.title == "Backend Engineer"
    assert job.company == "Acme PH"
    assert job.location == "Taguig, PH"


@respx.mock
def test_fetch_job_posting_returns_none_without_jsonld() -> None:
    respx.get("https://example.com/job/2").mock(
        return_value=httpx.Response(200, text="<html><body>no data here</body></html>")
    )

    assert fetch_job_posting("https://example.com/job/2") is None


@respx.mock
def test_fetch_job_posting_returns_none_when_blocked() -> None:
    respx.get("https://example.com/job/3").mock(return_value=httpx.Response(403))

    assert fetch_job_posting("https://example.com/job/3") is None
