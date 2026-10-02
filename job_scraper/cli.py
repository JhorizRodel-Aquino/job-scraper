"""CLI entry point: scrape, query, export."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Optional

import typer

from job_scraper.classify import classify_sub_role
from job_scraper.db import (
    DEFAULT_DB_PATH,
    compute_job_id,
    get_connection,
    init_db,
    query_jobs,
    upsert_job,
)
from job_scraper.models import Job
from job_scraper.pipeline import run as run_pipeline

app = typer.Typer(help="Scheduled crawler for software engineering job postings.")


@app.command()
def scrape(
    db_path: Path = typer.Option(DEFAULT_DB_PATH, help="Path to the SQLite database."),
) -> None:
    """Fetch every configured source, classify, and store/dedupe into the DB."""
    conn = get_connection(db_path)
    init_db(conn)
    counts = run_pipeline(conn)
    conn.close()

    total = sum(counts.values())
    typer.echo(f"Stored/updated {total} relevant jobs:")
    for source, count in counts.items():
        typer.echo(f"  {source}: {count}")


@app.command()
def ingest(
    url: str = typer.Argument(..., help="Job posting URL you found manually."),
    db_path: Path = typer.Option(DEFAULT_DB_PATH, help="Path to the SQLite database."),
) -> None:
    """Scrape a single job posting URL (schema.org JobPosting data) and store it.

    No relevance/location filtering — you already chose this specific
    posting by pasting its URL, so it's stored as-is (sub_role is still
    classified from the title for consistent querying).
    """
    from job_scraper.ingest import fetch_job_posting

    raw = fetch_job_posting(url)
    if raw is None:
        typer.echo("Could not extract job data from that URL.", err=True)
        raise typer.Exit(code=1)

    job = Job(**raw.model_dump(), id=compute_job_id(raw), sub_role=classify_sub_role(raw.title))

    conn = get_connection(db_path)
    init_db(conn)
    upsert_job(conn, job)
    conn.commit()
    conn.close()

    typer.echo(f"Stored: [{job.sub_role}] {job.title} @ {job.company}")


def _row_to_dict(row) -> dict:
    return {key: row[key] for key in row.keys()}


def _collect_rows(
    db_path: Path,
    role: Optional[str],
    remote: Optional[bool],
    since_days: Optional[int],
    include_stale: bool,
) -> list[dict]:
    conn = get_connection(db_path)
    rows = query_jobs(
        conn, role=role, remote=remote, since_days=since_days, include_stale=include_stale
    )
    conn.close()
    return [_row_to_dict(row) for row in rows]


@app.command()
def query(
    role: Optional[str] = typer.Option(
        None, help="Filter by sub_role: frontend, backend, full-stack, devops, mobile, other."
    ),
    remote: Optional[bool] = typer.Option(None, help="Filter by remote (true/false)."),
    since_days: Optional[int] = typer.Option(
        None, "--since", help="Only jobs last seen within this many days."
    ),
    include_stale: bool = typer.Option(
        False, help="Include postings not seen recently (see STALE_AFTER_DAYS)."
    ),
    limit: int = typer.Option(50, help="Max rows to print."),
    db_path: Path = typer.Option(DEFAULT_DB_PATH, help="Path to the SQLite database."),
) -> None:
    """Filter and print stored jobs."""
    rows = _collect_rows(db_path, role, remote, since_days, include_stale)[:limit]
    if not rows:
        typer.echo("No matching jobs.")
        return
    for row in rows:
        remote_tag = "remote" if row["remote"] else row["location"] or "?"
        typer.echo(
            f"[{row['sub_role'] or '-'}] {row['title']} @ {row['company']} "
            f"({remote_tag}) - {row['url']}"
        )
    typer.echo(f"\n{len(rows)} shown (use --limit to see more).")


@app.command()
def export(
    output: Path = typer.Option(..., help="Output file path."),
    format: str = typer.Option("csv", help="csv or json"),
    role: Optional[str] = typer.Option(None, help="Filter by sub_role."),
    remote: Optional[bool] = typer.Option(None, help="Filter by remote (true/false)."),
    since_days: Optional[int] = typer.Option(
        None, "--since", help="Only jobs last seen within this many days."
    ),
    include_stale: bool = typer.Option(False, help="Include stale postings."),
    db_path: Path = typer.Option(DEFAULT_DB_PATH, help="Path to the SQLite database."),
) -> None:
    """Export filtered jobs to CSV or JSON."""
    rows = _collect_rows(db_path, role, remote, since_days, include_stale)
    if format not in ("csv", "json"):
        typer.echo("format must be 'csv' or 'json'", err=True)
        raise typer.Exit(code=1)

    if format == "json":
        output.write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
    else:
        if not rows:
            output.write_text("", encoding="utf-8")
        else:
            with output.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)

    typer.echo(f"Exported {len(rows)} jobs to {output}")


if __name__ == "__main__":
    app()
