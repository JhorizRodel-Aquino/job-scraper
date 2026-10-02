"""Streamlit UI: browse stored jobs in a table, click a row for full details,
paste a URL to manually ingest a posting (the `ingest` CLI command, same code).

Run with: streamlit run job_scraper/ui.py
"""

from __future__ import annotations

import html
import json

import pandas as pd
import streamlit as st

from job_scraper.classify import classify_sub_role
from job_scraper.db import (
    DEFAULT_DB_PATH,
    compute_job_id,
    get_connection,
    init_db,
    query_jobs,
    upsert_job,
)
from job_scraper.ingest import fetch_job_posting
from job_scraper.models import Job

st.set_page_config(page_title="Job Scraper", layout="wide")

# st.dialog only offers width="small" (500px) or "large" (~1000px); this
# splits the difference since neither fit well for a job description.
st.markdown(
    '<style>div[role="dialog"] { width: 700px !important; }</style>',
    unsafe_allow_html=True,
)

conn = get_connection(DEFAULT_DB_PATH)
init_db(conn)

TABLE_KEY = "jobs_table"


@st.dialog("Job details")
def show_job_dialog(job: dict) -> None:
    st.subheader(f"{job['title']} @ {job['company']}")
    st.caption(
        f"Sub-role: {job['sub_role'] or '-'}  |  Location: {job['location'] or '-'}  |  "
        f"Remote: {'Yes' if job['remote'] else 'No'}  |  Source: {job['source']}  |  "
        f"First seen: {job['first_seen_at']}  |  Last seen: {job['last_seen_at']}"
    )
    st.markdown(f"[Open original posting]({job['url']})")
    if job.get("salary_min") or job.get("salary_max"):
        st.write(f"**Salary:** {job.get('salary_min') or '?'} - {job.get('salary_max') or '?'}")

    st.markdown("#### Description")
    description = job.get("description")
    if description:
        st.markdown(html.unescape(description), unsafe_allow_html=True)
    else:
        st.caption("No description stored.")

    with st.expander("Raw source payload"):
        try:
            st.json(json.loads(job.get("raw_json") or "{}"))
        except json.JSONDecodeError:
            st.text(job.get("raw_json"))

    if st.button("Close"):
        st.session_state[TABLE_KEY] = {"selection": {"rows": [], "columns": []}}
        st.rerun()


st.title("Job Scraper")

with st.form("ingest_form", clear_on_submit=True):
    url = st.text_input("Paste a job posting URL to scrape and store it")
    submitted = st.form_submit_button("Ingest")

if submitted and url:
    with st.spinner("Fetching..."):
        raw = fetch_job_posting(url)
    if raw is None:
        st.error("Could not extract job data from that URL.")
    else:
        job = Job(**raw.model_dump(), id=compute_job_id(raw), sub_role=classify_sub_role(raw.title))
        upsert_job(conn, job)
        conn.commit()
        st.success(f"Stored: [{job.sub_role}] {job.title} @ {job.company}")

st.divider()

col1, col2, col3, col4 = st.columns(4)
with col1:
    role = st.selectbox(
        "Role", ["(any)", "frontend", "backend", "full-stack", "devops", "mobile", "other"]
    )
with col2:
    remote_choice = st.selectbox("Remote", ["(any)", "Remote only", "On-site only"])
with col3:
    since_days = st.number_input("Seen within (days)", min_value=0, value=0, step=1)
with col4:
    include_stale = st.checkbox("Include stale")

rows = query_jobs(
    conn,
    role=None if role == "(any)" else role,
    remote=None if remote_choice == "(any)" else remote_choice == "Remote only",
    since_days=since_days or None,
    include_stale=include_stale,
)
jobs = [dict(r) for r in rows]

if not jobs:
    st.info("No matching jobs.")
else:
    df = pd.DataFrame(jobs)
    display_cols = ["title", "company", "sub_role", "location", "remote", "url", "last_seen_at"]
    event = st.dataframe(
        df[display_cols],
        hide_index=True,
        width="stretch",
        on_select="rerun",
        selection_mode="single-row",
        key=TABLE_KEY,
        column_config={"url": st.column_config.LinkColumn("Link")},
    )
    selected_rows = event.selection.rows if event.selection else []

    if selected_rows:
        show_job_dialog(jobs[selected_rows[0]])
