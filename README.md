# Job Scraper

A scheduled crawler that collects software engineering job postings (frontend,
backend, full-stack, devops, mobile) in the **Philippines** from free API/feed
sources into a local SQLite database, with a CLI to query and export what it
finds.

Standalone project — not wired into any other app's database.

## Sources (v1)

API/feed-based sources only, no anti-bot scraping. Every job, regardless of
source, is also checked against `config.PH_LOCATION_KEYWORDS`
(`classify.is_philippines`) and dropped if its location doesn't look
Philippines-based — company boards below post globally, this is what keeps
the DB PH-only.

- [Jooble](https://jooble.org/api/about) — job aggregator API, queried scoped
  to `location: "Philippines"` (requires a free API key)
- [Greenhouse](https://boards-api.greenhouse.io) — per-company boards, limited
  to companies confirmed to post PH jobs (seed list in `job_scraper/config.py`)
- [Lever](https://api.lever.co) — per-company boards, same PH-confirmed-only
  seeding

Other candidate sources (Ashby per-company boards, RemoteOK, WeWorkRemotely,
Arbeitnow, USAJobs, Adzuna) were evaluated and dropped: no PH-posting company
was found on Ashby, the others are globally-scoped aggregators with no way
to filter to PH, and Adzuna/USAJobs don't cover PH at all.

LinkedIn/Indeed/Glassdoor-style *automated crawling* of those sites is
deliberately out of scope — see `HANDOFF.md` for the tradeoff. What's in
scope instead is manual, single-URL ingestion (see `ingest` below): you find
a posting yourself, paste its URL, the tool captures the structured data.

## Manual ingestion (`ingest`)

```powershell
.\.venv\Scripts\python -m job_scraper ingest "<job posting URL>"
```

Parses the `schema.org JobPosting` JSON-LD block the page embeds for Google
Jobs indexing — not site-specific, works for anything using that markup.
Confirmed working (tested live) for LinkedIn's public guest job pages, no
login required. Jobstreet and Indeed block even a single plain request
(Cloudflare-style bot protection) — `ingest` falls back to a real headless
browser via Playwright for those, but it's not installed by default:

```powershell
.\.venv\Scripts\pip install -e ".[browser]"
.\.venv\Scripts\playwright install chromium
```

Without that extra installed, sites that block plain requests simply fail
to ingest ("Could not extract job data from that URL").

Unlike `scrape`, `ingest` does **not** filter by relevance or PH location —
you already chose that specific posting by pasting its URL, so it's stored
as-is (sub_role is still classified from the title for consistent
querying).

## UI

A local browser UI over the same database — a sortable table (title,
company, sub-role, location, link, last seen), click a row to see the full
scraped description, plus the same paste-a-URL ingest box as the CLI.

```powershell
.\.venv\Scripts\pip install -e ".[ui]"
.\.venv\Scripts\streamlit run job_scraper/ui.py
```

Opens at http://localhost:8501.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -e ".[dev]"
```

Jooble is optional; without `JOOBLE_API_KEY` that source is silently skipped
(Greenhouse/Lever need no key and still run). To enable Jooble, copy
`.env.example` to `.env` and fill in the key from
https://jooble.org/api/about.

## Usage

```powershell
# Fetch all sources, classify, and store/dedupe into jobs.db
.\.venv\Scripts\python -m job_scraper scrape

# Filter stored jobs
.\.venv\Scripts\python -m job_scraper query --role backend --remote --since 7

# Export to CSV or JSON
.\.venv\Scripts\python -m job_scraper export --output jobs.csv --format csv --role devops
```

Run `... query --help` / `... export --help` for the full filter list, or see
[`CLI.md`](CLI.md) for a complete reference with examples for every command.

## Scheduling

`scripts/register_task.ps1` registers a daily Windows Task Scheduler entry
that runs `scrape`. It is not run automatically — review it, then run it
yourself from an elevated PowerShell prompt:

```powershell
.\scripts\register_task.ps1
```

## Tests

```powershell
.\.venv\Scripts\python -m pytest
```

## Adding a new source

1. Add a module under `job_scraper/sources/` exposing `NAME: str` and
   `fetch() -> list[RawJob]` (see `job_scraper/sources/base.py`).
2. Register it in `job_scraper/sources/__init__.py`'s `ALL_SOURCES` list.
3. If it's a per-company board API (like Greenhouse/Lever), manually check
   the board actually has PH postings before seeding the company into
   `job_scraper/config.py` — `pipeline.normalize_and_classify` will filter
   non-PH jobs out regardless, but there's no point fetching companies with
   zero PH postings.

## Roadmap

- FastAPI read endpoint over the same SQLite DB (deferred until the CLI
  pipeline is validated against real data).
- Revisit scraping harder, anti-bot-defended sites (LinkedIn, Jobstreet,
  Indeed, Glassdoor) explicitly, site by site.
