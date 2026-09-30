# Job Scraper

A scheduled crawler that collects software engineering job postings (frontend,
backend, full-stack, devops, mobile) from free API/feed sources into a local
SQLite database, with a CLI to query and export what it finds.

Standalone project — not wired into any other app's database.

## Sources (v1)

API/feed-based sources only, no anti-bot scraping:

- [Greenhouse](https://boards-api.greenhouse.io) — per-company boards (seed list in `job_scraper/config.py`)
- [Lever](https://api.lever.co) — per-company boards
- [Ashby](https://api.ashbyhq.com) — per-company boards
- [RemoteOK](https://remoteok.com/api) — global remote listings
- [WeWorkRemotely](https://weworkremotely.com) — RSS feeds (programming, devops/sysadmin)
- [Arbeitnow](https://www.arbeitnow.com/api/job-board-api) — global listings
- [USAJobs](https://developer.usajobs.gov/) — US federal jobs (requires a free API key)

LinkedIn/Indeed/Glassdoor-style scraping of anti-bot-defended sites is
deliberately out of scope for v1 — see `HANDOFF.md` for the tradeoff.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -e ".[dev]"
```

USAJobs is optional; without it that source is silently skipped. To enable it,
copy `.env.example` to `.env` and fill in `USAJOBS_API_KEY` /
`USAJOBS_USER_AGENT` (your registered email) from
https://developer.usajobs.gov/apirequest/.

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
3. If it's a per-company board API (like Greenhouse/Lever/Ashby), add a
   company seed list to `job_scraper/config.py`.

## Roadmap

- FastAPI read endpoint over the same SQLite DB (deferred until the CLI
  pipeline is validated against real data).
- Revisit scraping harder, anti-bot-defended sites (LinkedIn, Indeed,
  Glassdoor) explicitly, site by site.
