"""Static configuration: classification keyword lists, source seed lists, tunables."""

from __future__ import annotations

# A job title must match at least one of these to be considered a software
# engineering role at all. Keeps non-eng postings from broad feeds (RemoteOK,
# WeWorkRemotely) out of the database entirely.
GENERAL_SWE_KEYWORDS = [
    "software engineer",
    "swe",
    "developer",
    "programmer",
    "software architect",
    "sde",
    "engineer i",
    "engineer ii",
    "engineer iii",
]

# Checked in order; first match wins. Keep more specific roles before
# "full-stack" so e.g. "Senior Backend Engineer" doesn't fall through.
SUB_ROLE_KEYWORDS: list[tuple[str, list[str]]] = [
    (
        "devops",
        [
            "devops",
            "sre",
            "site reliability",
            "platform engineer",
            "infrastructure engineer",
            "kubernetes",
            "terraform",
            "cloud engineer",
        ],
    ),
    (
        "mobile",
        [
            "ios",
            "android",
            "mobile engineer",
            "mobile developer",
            "react native",
            "flutter",
            "swift developer",
            "kotlin developer",
        ],
    ),
    (
        "frontend",
        [
            "frontend",
            "front-end",
            "front end",
            "react developer",
            "vue developer",
            "angular developer",
            "ui engineer",
            "web developer",
        ],
    ),
    (
        "backend",
        [
            "backend",
            "back-end",
            "back end",
            "api engineer",
            "server engineer",
            "database engineer",
        ],
    ),
    (
        "full-stack",
        [
            "full stack",
            "full-stack",
            "fullstack",
        ],
    ),
]

# A job not matched to any specific sub-role above, but that passed the
# general SWE relevance filter, is stored with this fallback.
DEFAULT_SUB_ROLE = "other"

# Number of days without seeing a posting again before it's considered stale
# by default in query/export (still kept in the DB, just filtered out).
STALE_AFTER_DAYS = 14

# A job's location must match one of these (case-insensitive substring) to
# be considered Philippines-based. Company ATS boards list PH postings as a
# city/province without the word "Philippines" (e.g. "Clark, Pampanga"), so
# this needs the major cities/provinces, not just the country name.
PH_LOCATION_KEYWORDS = [
    "philippines",
    "manila",
    "makati",
    "quezon city",
    "taguig",
    "pasig",
    "bgc",
    "cebu",
    "davao",
    "clark",
    "pampanga",
    "iloilo",
    "baguio",
    "cavite",
    "laguna",
    "bulacan",
    "angeles city",
]

# Greenhouse board tokens confirmed (by manual check) to currently post jobs
# located in the Philippines.
GREENHOUSE_COMPANIES = [
    "hellofresh",
    "5ca",
    "cteph",
    "wundermanthompson",
]

# Lever site tokens confirmed to currently post jobs located in the
# Philippines.
LEVER_COMPANIES = [
    "Aprio",
]
