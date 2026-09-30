# Job Scraper — handoff brief

Context carried over from a conversation in the `Resume-Builder` project (a Claude-powered resume tailoring app with a Jobs tracker tab). This new repo is a **separate, standalone project** meant to eventually feed job listings that Resume-Builder (or anything else) can consume — but it is not wired into that repo's code or database.

## Goal
A complex scraper/crawler that finds software engineering jobs worldwide across all major sub-roles: frontend, backend, full-stack, devops, mobile.

## Decisions made so far (via user's answers to clarifying questions)

1. **Source strategy: scrape everything, including sites without public APIs (LinkedIn, Indeed, Glassdoor, etc.)**
   - User explicitly chose the broadest-coverage option over the recommended "APIs/feeds only" or "hybrid" approaches.
   - Note: this was flagged as carrying real ToS and legal/account-ban risk, and needing anti-bot handling. User chose to proceed anyway — revisit this tradeoff explicitly before writing scrapers for specific sites, since some (e.g. LinkedIn) are aggressively defended and litigious about scraping.
   - Still worth layering in the free/legit sources (Greenhouse, Lever, Ashby, RemoteOK, WeWorkRemotely, Arbeitnow, USAJobs, etc.) as a reliable base layer, with scraping added on top for sites without APIs.

2. **Standalone project, separate repo/entity** (this repo: `C:\Users\jhoriz\Documents\Job-Scraper`)
   - Not integrated into Resume-Builder's codebase or database.
   - Own repo, own stack, own DB.

3. **Run mode: scheduled crawler + stored database**
   - Not just on-demand search — runs periodically (cron/scheduler), stores and dedupes jobs over time, supports querying historical + new postings.
   - Implies needing: a scheduler, persistent storage, dedup logic, staleness/expiry handling for old postings.

## Not yet decided (next planning steps)
- Tech stack (language/framework for the crawler, storage engine — SQLite vs Postgres vs something else).
- Which specific sites/sources to target first, and in what order.
- How results get exposed (REST API? Search UI? Export? Direct feed into Resume-Builder's DB later?).
- Anti-bot/scale approach for the harder sites (headless browser, proxies, rate limiting) — and a clear line on which sites are in-scope vs too risky.
- Filtering/classification logic for sub-roles (frontend/backend/full-stack/devops/mobile) and "software engineering" relevance in general.
- Scheduling cadence and infrastructure (where does the cron job run — local machine, cloud, etc.).

## Suggested next step
Start a new Claude Code session in this folder and begin with `/plan` (or ask Claude to enter plan mode) to work through the undecided items above before writing any code.
