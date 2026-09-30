from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel


class RawJob(BaseModel):
    """What a source adapter returns before classification/storage."""

    source: str
    external_id: str | None = None
    title: str
    company: str
    location: str | None = None
    remote: bool = False
    url: str
    description: str | None = None
    posted_date: date | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    raw: dict[str, Any] = {}


class Job(RawJob):
    """A RawJob after classification, as stored in the database."""

    id: str
    sub_role: str | None = None
