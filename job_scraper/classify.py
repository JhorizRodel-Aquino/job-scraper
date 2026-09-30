"""Keyword-based relevance filtering and sub-role classification."""

from __future__ import annotations

from job_scraper.config import DEFAULT_SUB_ROLE, GENERAL_SWE_KEYWORDS, SUB_ROLE_KEYWORDS


def is_relevant(title: str) -> bool:
    """True if the title looks like a software engineering role at all."""
    lowered = title.lower()
    return any(keyword in lowered for keyword in GENERAL_SWE_KEYWORDS)


def classify_sub_role(title: str) -> str:
    """Best-matching sub-role for a title, or DEFAULT_SUB_ROLE if none match."""
    lowered = title.lower()
    for sub_role, keywords in SUB_ROLE_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return sub_role
    return DEFAULT_SUB_ROLE
