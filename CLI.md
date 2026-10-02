# CLI reference

All commands run as `python -m job_scraper <command> [options]`. Activate the
venv first so `python` resolves to the project's interpreter:

```powershell
.\.venv\Scripts\Activate.ps1
```

(Or skip activation and call `.\.venv\Scripts\python.exe -m job_scraper ...`
directly every time.)

Every command accepts `--db-path <path>` to point at a different SQLite file;
it defaults to `jobs.db` in the repo root.

---

## `scrape`

Fetches every configured source (Jooble, Greenhouse, Lever), filters to
relevant software engineering roles located in the Philippines, classifies
sub-role, and upserts into the database. Safe to run repeatedly — matching
postings are deduped and just get their `last_seen_at` bumped rather than
duplicated.

```powershell
python -m job_scraper scrape
python -m job_scraper scrape --db-path D:\data\jobs.db
```

Prints a per-source count of jobs stored/updated. A source that fails (rate
limit, network error, etc.) is skipped for that run rather than aborting the
whole scrape — its count shows `0`.

---

## `ingest`

Scrapes a single job posting URL you found manually (e.g. browsing LinkedIn
yourself) and stores it. Parses the `schema.org JobPosting` JSON-LD the page
embeds for Google Jobs indexing — works for any site using that markup, not
just LinkedIn.

```powershell
python -m job_scraper ingest "<job posting URL>"
python -m job_scraper ingest "<job posting URL>" --db-path D:\data\jobs.db
```

No relevance or PH-location filtering is applied — pasting the URL *is* the
filter, since you already chose that specific posting. `sub_role` is still
classified from the title for consistent querying.

Sites that block a plain HTTP request (confirmed: Jobstreet, Indeed) need
the optional Playwright fallback:

```powershell
pip install -e ".[browser]"
playwright install chromium
```

Without it, those URLs fail with "Could not extract job data from that
URL."

---

## `query`

Filters and prints stored jobs to the terminal.

```powershell
python -m job_scraper query [OPTIONS]
```

| Option | Description |
|---|---|
| `--role <role>` | Filter by sub-role: `frontend`, `backend`, `full-stack`, `devops`, `mobile`, `other`. |
| `--remote` / `--no-remote` | Only remote, or only non-remote, postings. Omit to include both. |
| `--since <days>` | Only jobs last seen within the given number of days. |
| `--include-stale` / `--no-include-stale` | Include postings not re-seen in 14+ days (default: excluded). |
| `--limit <n>` | Max rows to print. Default `50`. |
| `--db-path <path>` | Database file. Default `jobs.db`. |

Examples:

```powershell
python -m job_scraper query --role backend
python -m job_scraper query --role devops --remote
python -m job_scraper query --role frontend --limit 20
python -m job_scraper query --since 3
python -m job_scraper query --include-stale --role mobile
```

Output format, one line per job:

```
[sub_role] Title @ Company (remote|location) - url
```

---

## `export`

Same filters as `query`, but writes the full result set (including
description, salary range, and raw source payload) to a file instead of
printing a trimmed view.

```powershell
python -m job_scraper export --output <path> [OPTIONS]
```

| Option | Description |
|---|---|
| `--output <path>` | **Required.** Output file path. |
| `--format <csv\|json>` | Output format. Default `csv`. |
| `--role <role>` | Same as `query`. |
| `--remote` / `--no-remote` | Same as `query`. |
| `--since <days>` | Same as `query`. |
| `--include-stale` / `--no-include-stale` | Same as `query`. |
| `--db-path <path>` | Database file. Default `jobs.db`. |

Examples:

```powershell
python -m job_scraper export --output jobs.csv --format csv --role backend
python -m job_scraper export --output jobs.json --format json --remote
python -m job_scraper export --output devops_recent.csv --role devops --since 7
```

---

## Getting `--help` for anything

```powershell
python -m job_scraper --help
python -m job_scraper scrape --help
python -m job_scraper ingest --help
python -m job_scraper query --help
python -m job_scraper export --help
```
