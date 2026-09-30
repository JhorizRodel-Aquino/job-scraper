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

# Greenhouse board tokens (boards-api.greenhouse.io/v1/boards/{token}/jobs).
# Starter list of well-known companies on the platform; expand over time.
GREENHOUSE_COMPANIES = [
    "stripe",
    "airbnb",
    "robinhood",
    "doordash",
    "coinbase",
    "asana",
    "gitlab",
    "figma",
]

# Lever site tokens (api.lever.co/v0/postings/{token}).
LEVER_COMPANIES = [
    "netflix",
    "shopify",
    "palantir",
    "plaid",
    "brex",
]

# Ashby job-board names (api.ashbyhq.com/posting-api/job-board/{name}).
ASHBY_COMPANIES = [
    "ramp",
    "linear",
    "notion",
    "vercel",
]
